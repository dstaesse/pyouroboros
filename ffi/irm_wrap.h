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
