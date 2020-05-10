/*
 * Ouroboros - Copyright (C) 2016 - 2020
 *
 * An fccntl wrapper
 *
 *    Dimitri Staessens <dimitri.staessens@ugent.be>
 *    Sander Vrijders   <sander.vrijders@ugent.be>
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

#include <ouroboros/fccntl.h>

int flow_set_snd_timeout(int fd, struct timespec * ts)
{
        return fccntl(fd, FLOWSSNDTIMEO, ts);
}

int flow_set_rcv_timeout(int fd, struct timespec * ts)
{
        return fccntl(fd, FLOWSRCVTIMEO, ts);
}

int flow_get_snd_timeout(int fd, struct timespec * ts)
{
        return fccntl(fd, FLOWGSNDTIMEO, ts);
}

int flow_get_rcv_timeout(int fd, struct timespec * ts)
{
        return fccntl(fd, FLOWGRCVTIMEO, ts);
}

int flow_get_qos(int fd, qosspec_t * qs)
{
        return fccntl(fd, FLOWGQOSSPEC, qs);
}

int flow_get_rx_qlen(int fd, size_t * sz)
{
        return fccntl(fd, FLOWGRXQLEN, sz);
}

int flow_get_tx_qlen(int fd, size_t * sz)
{
        return fccntl(fd, FLOWGTXQLEN, sz);
}

int flow_set_flags(int fd, uint32_t flags)
{
        return fccntl(fd, FLOWSFLAGS, flags);
}

int flow_get_flags(int fd)
{
        uint32_t flags;

        if (fccntl(fd, FLOWGFLAGS, &flags))
                return -EPERM;

        return (int) flags;
}
