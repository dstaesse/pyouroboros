#
# Ouroboros - Copyright (C) 2016 - 2020
#
# Python API for applications
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
/* OUROBOROS QOS.H */
typedef struct qos_spec {
        uint32_t delay;         /* In ms */
        uint64_t bandwidth;     /* In bits/s */
        uint8_t  availability;  /* Class of 9s */
        uint32_t loss;          /* Packet loss */
        uint32_t ber;           /* Bit error rate, errors per billion bits */
        uint8_t  in_order;      /* In-order delivery, enables FRCT */
        uint32_t max_gap;       /* In ms */
        uint16_t cypher_s;      /* Cypher strength, 0 = no encryption */
} qosspec_t;

/* OUROBOROS DEV.H */
/* Returns flow descriptor, qs updates to supplied QoS. */
int     flow_alloc(const char *            dst_name,
                   qosspec_t *             qs,
                   const struct timespec * timeo);

/* Returns flow descriptor, qs updates to supplied QoS. */
int     flow_accept(qosspec_t *             qs,
                    const struct timespec * timeo);

/* Returns flow descriptor, qs updates to supplied QoS. */
int     flow_join(const char *            bc,
                  qosspec_t *             qs,
                  const struct timespec * timeo);

int     flow_dealloc(int fd);

ssize_t flow_write(int          fd,
                   const void * buf,
                   size_t       count);

ssize_t flow_read(int    fd,
                  void * buf,
                  size_t count);

/*OUROBOROS FCCNTL.H, VIA WRAPPER */
int flow_set_snd_timeout(int fd, struct timespec * ts);

int flow_set_rcv_timeout(int fd, struct timespec * ts);

int flow_get_snd_timeout(int fd, struct timespec * ts);

int flow_get_rcv_timeout(int fd, struct timespec * ts);

int flow_get_qos(int fd, qosspec_t * qs);

int flow_get_rx_qlen(int fd, size_t * sz);

int flow_get_tx_qlen(int fd, size_t * sz);

int flow_set_flags(int fd, uint32_t flags);

int flow_get_flags(int fd);

/*OUROBOROS FQUEUE.H */
enum fqtype {
        FLOW_PKT     = (1 << 0),
        FLOW_DOWN    = (1 << 1),
        FLOW_UP      = (1 << 2),
        FLOW_ALLOC   = (1 << 3),
        FLOW_DEALLOC = (1 << 4)
};

struct flow_set;

struct fqueue;

typedef struct flow_set fset_t;
typedef struct fqueue fqueue_t;

fset_t *    fset_create(void);

void        fset_destroy(fset_t * set);

fqueue_t *  fqueue_create(void);

void        fqueue_destroy(struct fqueue * fq);

void        fset_zero(fset_t * set);

int         fset_add(fset_t * set,
                     int      fd);

bool        fset_has(const fset_t * set,
                     int            fd);

void        fset_del(fset_t * set,
                     int      fd);

int         fqueue_next(fqueue_t * fq);

int         fqueue_type(fqueue_t * fq);

ssize_t     fevent(fset_t *                set,
                   fqueue_t *              fq,
                   const struct timespec * timeo);
""")

ffibuilder.set_source("_ouroboros_cffi",
                      """
#include "ouroboros/qos.h"
#include "ouroboros/dev.h"
#include "fccntl_wrap.h"
#include "ouroboros/fqueue.h"
                      """,
                      libraries=['ouroboros-dev'],
                      extra_compile_args=["-I./ffi/"])

if __name__ == "__main__":
    ffibuilder.compile(verbose=True)
