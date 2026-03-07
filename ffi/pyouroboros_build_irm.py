#
# Ouroboros - Copyright (C) 2016 - 2026
#
# Python API for Ouroboros
#
#    Dimitri Staessens <dimitri@ouroboros.rocks>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public License
# version 2.1 as published by the Free Software Foundation.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., http://www.fsf.org/about/contact/.
#

from cffi import FFI

ffibuilder: FFI = FFI()

ffibuilder.cdef("""
/* System types */
typedef int... pid_t;
typedef long... time_t;

struct timespec {
    time_t tv_sec;
    long   tv_nsec;
    ...;
};

/* OUROBOROS VERSION.H */
#define OUROBOROS_VERSION_MAJOR ...
#define OUROBOROS_VERSION_MINOR ...
#define OUROBOROS_VERSION_PATCH ...

/* Network types */
struct in_addr { ...; };
struct in6_addr { ...; };

/* OUROBOROS QOS.H */
typedef struct qos_spec {
        uint32_t delay;
        uint64_t bandwidth;
        uint8_t  availability;
        uint32_t loss;
        uint32_t ber;
        uint8_t  in_order;
        uint32_t max_gap;
        uint32_t timeout;       /* Timeout in ms */
} qosspec_t;

/* OUROBOROS IPCP.H */
enum ipcp_type {
        IPCP_LOCAL     = ...,
        IPCP_UNICAST   = ...,
        IPCP_BROADCAST = ...,
        IPCP_ETH_LLC   = ...,
        IPCP_ETH_DIX   = ...,
        IPCP_UDP4      = ...,
        IPCP_UDP6      = ...,
        IPCP_INVALID   = ...
};

/* Unicast IPCP policies */
enum pol_addr_auth {
        ADDR_AUTH_FLAT_RANDOM = ...,
        ADDR_AUTH_INVALID     = ...
};

enum pol_link_state {
        LS_SIMPLE  = ...,
        LS_LFA     = ...,
        LS_ECMP    = ...,
        LS_INVALID = ...
};

struct ls_config {
        enum pol_link_state pol;
        time_t              t_recalc;
        time_t              t_update;
        time_t              t_timeo;
};

enum pol_routing {
        ROUTING_LINK_STATE = ...,
        ROUTING_INVALID    = ...
};

struct routing_config {
        enum pol_routing pol;
        union {
                struct ls_config ls;
        };
};

enum pol_cong_avoid {
        CA_NONE    = ...,
        CA_MB_ECN  = ...,
        CA_INVALID = ...
};

struct dt_config {
        struct {
                uint8_t addr_size;
                uint8_t eid_size;
                uint8_t max_ttl;
        };
        struct routing_config routing;
};

enum pol_dir {
        DIR_DHT     = ...,
        DIR_INVALID = ...
};

enum pol_dir_hash {
        DIR_HASH_SHA3_224 = ...,
        DIR_HASH_SHA3_256 = ...,
        DIR_HASH_SHA3_384 = ...,
        DIR_HASH_SHA3_512 = ...,
        DIR_HASH_INVALID  = ...
};

struct dir_dht_config {
        struct {
                uint32_t alpha;
                uint32_t k;
                uint32_t t_expire;
                uint32_t t_refresh;
                uint32_t t_replicate;
        } params;
        uint64_t peer;
};

struct dir_config {
        enum pol_dir pol;
        union {
                struct dir_dht_config dht;
        };
};

struct uni_config {
        struct dt_config    dt;
        struct dir_config   dir;
        enum pol_addr_auth  addr_auth_type;
        enum pol_cong_avoid cong_avoid;
};

struct eth_config {
        char     dev[256]; /* DEV_NAME_SIZE + 1 */
        uint16_t ethertype;
};

struct udp4_config {
        struct in_addr ip_addr;
        struct in_addr dns_addr;
        uint16_t       port;
};

struct udp6_config {
        struct in6_addr ip_addr;
        struct in6_addr dns_addr;
        uint16_t        port;
};

struct layer_info {
        char              name[256]; /* LAYER_NAME_SIZE + 1 */
        enum pol_dir_hash dir_hash_algo;
};

struct ipcp_config {
        struct layer_info layer_info;
        enum ipcp_type    type;

        union {
                struct uni_config  unicast;
                struct udp4_config udp4;
                struct udp6_config udp6;
                struct eth_config  eth;
        };
};

/* OUROBOROS NAME.H */
#define BIND_AUTO ...

enum pol_balance {
        LB_RR      = ...,
        LB_SPILL   = ...,
        LB_INVALID = ...
};

struct name_sec_paths {
        char enc[512]; /* NAME_PATH_SIZE + 1 */
        char key[512]; /* NAME_PATH_SIZE + 1 */
        char crt[512]; /* NAME_PATH_SIZE + 1 */
};

struct name_info {
        char             name[256]; /* NAME_SIZE + 1 */
        enum pol_balance pol_lb;

        struct name_sec_paths s;
        struct name_sec_paths c;
};

/* OUROBOROS IRM.H */

struct ipcp_list_info {
        pid_t          pid;
        enum ipcp_type type;
        char           name[255]; /* NAME_SIZE */
        char           layer[255]; /* LAYER_NAME_SIZE */
};

pid_t   irm_create_ipcp(const char *   name,
                        enum ipcp_type type);

int     irm_destroy_ipcp(pid_t pid);

ssize_t irm_list_ipcps(struct ipcp_list_info ** ipcps);

int     irm_enroll_ipcp(pid_t        pid,
                        const char * dst);

int     irm_bootstrap_ipcp(pid_t                      pid,
                           const struct ipcp_config * conf);

int     irm_connect_ipcp(pid_t        pid,
                         const char * component,
                         const char * dst,
                         qosspec_t    qs);

int     irm_disconnect_ipcp(pid_t        pid,
                            const char * component,
                            const char * dst);

int     irm_bind_program(const char * prog,
                         const char * name,
                         uint16_t     opts,
                         int          argc,
                         char **      argv);

int     irm_unbind_program(const char * progr,
                           const char * name);

int     irm_bind_process(pid_t        pid,
                         const char * name);

int     irm_unbind_process(pid_t        pid,
                           const char * name);

int     irm_create_name(struct name_info * info);

int     irm_destroy_name(const char * name);

ssize_t irm_list_names(struct name_info ** names);

int     irm_reg_name(const char * name,
                     pid_t        pid);

int     irm_unreg_name(const char * name,
                       pid_t        pid);

/* IRM WRAPPER HELPERS */
int ipcp_config_udp4_set_ip(struct ipcp_config * conf,
                            const char *         ip_str);

int ipcp_config_udp4_set_dns(struct ipcp_config * conf,
                             const char *         dns_str);

int ipcp_config_udp6_set_ip(struct ipcp_config * conf,
                            const char *         ip_str);

int ipcp_config_udp6_set_dns(struct ipcp_config * conf,
                             const char *         dns_str);

/* libc */
void free(void *ptr);
""")

ffibuilder.set_source("_ouroboros_irm_cffi",
                      """
#include "ouroboros/version.h"
#include "ouroboros/qos.h"
#include "irm_wrap.h"
                      """,
                      libraries=['ouroboros-irm'],
                      extra_compile_args=["-I./ffi/"])

if __name__ == "__main__":
    ffibuilder.compile(verbose=True)
