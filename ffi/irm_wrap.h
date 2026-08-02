/*
 * Ouroboros - Copyright (C) 2016 - 2026
 *
 * An IRM wrapper for Python bindings
 *
 *    Dimitri Staessens <dimitri@ouroboros.rocks>
 *
 * This library is free software; you can redistribute it and/or
 * modify it under the terms of the GNU Lesser General Public License
 * version 2.1 as published by the Free Software Foundation.
 *
 * This library is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public
 * License along with this library; if not, write to the Free Software
 * Foundation, Inc., http://www.fsf.org/about/contact/.
 */

#include <ouroboros/irm.h>
#include <arpa/inet.h>
#include <stdio.h>
#include <string.h>

/* Length of "xx:xx:xx:xx:xx:xx". */
#define POA_MAC_STRLEN (3 * POA_MAC_SIZE - 1)

/*
 * poa_spec and poa_addr embed struct in_addr, which CFFI cannot
 * mirror; they stay opaque and are filled in here. A listed PoA
 * comes back as struct poa_spec_py, the same fields as text.
 */
struct poa_spec_py {
        int      type;
        char     addr[INET6_ADDRSTRLEN];
        uint16_t port;
        char     dev[DEV_NAME_SIZE + 1];
        char     mac[POA_MAC_STRLEN + 1];
        uint16_t ethertype;
};

static int poa_spec_set_udp(struct poa_spec * poa,
                            int               v6,
                            const char *      ip_str,
                            uint16_t          port)
{
        memset(poa, 0, sizeof(*poa));

        if (v6) {
                if (inet_pton(AF_INET6, ip_str, &poa->udp6.ip_addr) != 1)
                        return -1;
                poa->type      = POA_UDP6;
                poa->udp6.port = port;
                return 0;
        }

        if (inet_pton(AF_INET, ip_str, &poa->udp4.ip_addr) != 1)
                return -1;

        poa->type      = POA_UDP4;
        poa->udp4.port = port;

        return 0;
}

/* The PoA is named by dev; the mac is only reported by poa_spec_get. */
static int poa_spec_set_eth(struct poa_spec * poa,
                            const char *      dev,
                            uint16_t          ethertype)
{
        memset(poa, 0, sizeof(*poa));

        if (dev == NULL || strlen(dev) == 0)
                return -1;

        if (strlen(dev) > DEV_NAME_SIZE)
                return -1;

        poa->type          = POA_ETH;
        poa->eth.ethertype = ethertype;

        strcpy(poa->eth.dev, dev);

        return 0;
}

/* An all-zero MAC names nothing; the PoA goes by its device. */
static int poa_mac_is_set(const uint8_t * mac)
{
        size_t i;

        for (i = 0; i < POA_MAC_SIZE; i++) {
                if (mac[i] != 0)
                        return 1;
        }

        return 0;
}

/* Renders poas[idx] as text for the Python side. */
static int poa_spec_get(const struct poa_spec * poas,
                        size_t                  idx,
                        struct poa_spec_py *    out)
{
        const struct poa_spec * poa = poas + idx;

        memset(out, 0, sizeof(*out));

        out->type = (int) poa->type;

        switch (poa->type) {
        case POA_UDP4:
                if (inet_ntop(AF_INET, &poa->udp4.ip_addr, out->addr,
                              sizeof(out->addr)) == NULL)
                        return -1;
                out->port = poa->udp4.port;
                break;
        case POA_UDP6:
                if (inet_ntop(AF_INET6, &poa->udp6.ip_addr, out->addr,
                              sizeof(out->addr)) == NULL)
                        return -1;
                out->port = poa->udp6.port;
                break;
        case POA_ETH:
                memcpy(out->dev, poa->eth.dev, sizeof(out->dev));

                out->dev[sizeof(out->dev) - 1] = '\0';

                if (poa_mac_is_set(poa->eth.mac) != 0)
                        snprintf(out->mac, sizeof(out->mac),
                                 "%02x:%02x:%02x:%02x:%02x:%02x",
                                 poa->eth.mac[0], poa->eth.mac[1],
                                 poa->eth.mac[2], poa->eth.mac[3],
                                 poa->eth.mac[4], poa->eth.mac[5]);
                out->ethertype = poa->eth.ethertype;
                break;
        default:
                return -1;
        }

        return 0;
}

/*
 * Fills in addr for type. For UDP, dst is an IP literal or a host
 * name the IRMd resolves; for Ethernet the peer is resolved by name
 * query and our own PoA may be pinned by dev.
 */
static int poa_addr_set(struct poa_addr * addr,
                        int               type,
                        const char *      dst,
                        uint16_t          port,
                        uint16_t          ethertype,
                        const char *      dev)
{
        memset(addr, 0, sizeof(*addr));

        addr->type = (enum poa_type) type;
        if (type == POA_ETH) {
                addr->eth.src.ethertype = ethertype;
                addr->eth.dst.ethertype = ethertype;

                if (dev != NULL && strlen(dev) > 0) {
                        if (strlen(dev) > DEV_NAME_SIZE)
                                return -1;
                        strcpy(addr->eth.src.dev, dev);
                }

                return 0;
        }

        if (type != POA_UDP4 && type != POA_UDP6)
                return -1;

        if (type == POA_UDP4) {
                addr->udp4.port = port;
                if (inet_pton(AF_INET, dst, &addr->udp4.ip_addr) == 1)
                        return 0;
        } else {
                addr->udp6.port = port;
                if (inet_pton(AF_INET6, dst, &addr->udp6.ip_addr) == 1)
                        return 0;
        }

        if (strlen(dst) > POA_HOST_STRLEN)
                return -1;

        strcpy(addr->hostname, dst);

        return 0;
}
