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
#include <string.h>
#include <stdlib.h>

static int ipcp_config_udp4_set_ip(struct ipcp_config * conf,
                                   const char *         ip_str)
{
        return inet_pton(AF_INET, ip_str, &conf->udp4.ip_addr) == 1 ? 0 : -1;
}

static int ipcp_config_udp4_set_dns(struct ipcp_config * conf,
                                    const char *         dns_str)
{
        return inet_pton(AF_INET, dns_str, &conf->udp4.dns_addr) == 1 ? 0 : -1;
}

static int ipcp_config_udp6_set_ip(struct ipcp_config * conf,
                                   const char *         ip_str)
{
        return inet_pton(AF_INET6, ip_str, &conf->udp6.ip_addr) == 1 ? 0 : -1;
}

static int ipcp_config_udp6_set_dns(struct ipcp_config * conf,
                                    const char *         dns_str)
{
        return inet_pton(AF_INET6, dns_str, &conf->udp6.dns_addr) == 1 ? 0 : -1;
}

static void ipcp_config_init_uni(struct ipcp_config * conf,
                                 uint8_t addr_size, uint8_t eid_size,
                                 uint8_t max_ttl,
                                 enum pol_link_state ls_pol,
                                 long t_recalc, long t_update, long t_timeo,
                                 enum pol_dir dir_pol,
                                 uint32_t dht_alpha, uint32_t dht_k,
                                 uint32_t dht_t_expire, uint32_t dht_t_refresh,
                                 uint32_t dht_t_replicate,
                                 enum pol_addr_auth addr_auth,
                                 enum pol_cong_avoid cong_avoid)
{
        memset(conf, 0, sizeof(*conf));
        conf->type = IPCP_UNICAST;
        conf->unicast.dt.addr_size = addr_size;
        conf->unicast.dt.eid_size = eid_size;
        conf->unicast.dt.max_ttl = max_ttl;
        conf->unicast.dt.routing.pol = ROUTING_LINK_STATE;
        conf->unicast.dt.routing.ls.pol = ls_pol;
        conf->unicast.dt.routing.ls.t_recalc = t_recalc;
        conf->unicast.dt.routing.ls.t_update = t_update;
        conf->unicast.dt.routing.ls.t_timeo = t_timeo;
        conf->unicast.dir.pol = dir_pol;
        conf->unicast.dir.dht.params.alpha = dht_alpha;
        conf->unicast.dir.dht.params.k = dht_k;
        conf->unicast.dir.dht.params.t_expire = dht_t_expire;
        conf->unicast.dir.dht.params.t_refresh = dht_t_refresh;
        conf->unicast.dir.dht.params.t_replicate = dht_t_replicate;
        conf->unicast.addr_auth_type = addr_auth;
        conf->unicast.cong_avoid = cong_avoid;
}

static void ipcp_config_init_eth(struct ipcp_config * conf,
                                 const char *         dev,
                                 uint16_t             ethertype)
{
        memset(conf, 0, sizeof(*conf));
        strncpy(conf->eth.dev, dev, DEV_NAME_SIZE);
        conf->eth.ethertype = ethertype;
}
