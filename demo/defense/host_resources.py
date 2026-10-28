"""Pure host resource and subnet checks for the laptop Docker pilot preflight."""
import ipaddress

HOST_RESERVE_MIB=3072
MIN_FREE_DISK_MIB=20480
MAX_SWAP_PAGES_PER_SECOND=50


def swap_rate(first,second,seconds):
    """Return swapped pages per second between two (pswpin, pswpout) samples."""
    if type(seconds) not in (int,float) or seconds<=0:
        raise ValueError('Invalid swap sampling interval')
    for sample in (first,second):
        if not isinstance(sample,tuple) or len(sample)!=2 or any(type(v) is not int or v<0 for v in sample):
            raise ValueError('Invalid swap counters')
    swapped_in=second[0]-first[0]
    swapped_out=second[1]-first[1]
    if swapped_in<0 or swapped_out<0:
        raise ValueError('Swap counters went backwards')
    return (swapped_in+swapped_out)/seconds


def check_host_resources(available_mib,free_disk_mib,rate):
    """Require the host reserve in RAM, free disk for logs/snapshots and no swap thrash."""
    for value in (available_mib,free_disk_mib):
        if type(value) is not int or value<0:
            raise ValueError('Resource inventory is invalid')
    if type(rate) not in (int,float) or rate<0:
        raise ValueError('Resource inventory is invalid')
    if available_mib<HOST_RESERVE_MIB:
        raise ValueError(f'Insufficient RAM: need {HOST_RESERVE_MIB} MiB available, observed {available_mib} MiB')
    if free_disk_mib<MIN_FREE_DISK_MIB:
        raise ValueError(f'Insufficient disk: need {MIN_FREE_DISK_MIB} MiB free, observed {free_disk_mib} MiB')
    if rate>MAX_SWAP_PAGES_PER_SECOND:
        raise ValueError(f'Swap thrash: {rate:.0f} pages per second')
    return True


def reject_foreign_overlaps(occupied,owned_subnet):
    """Allow the owned subnet exactly once; any other overlapping range is a collision."""
    owned=ipaddress.ip_network(owned_subnet)
    count=0
    for value in occupied:
        try:
            network=ipaddress.ip_network(value,strict=False)
        except (TypeError,ValueError):
            raise ValueError('Network inventory is invalid or incomplete') from None
        if network==owned:
            count+=1
        elif network.version==4 and network.overlaps(owned):
            raise ValueError('Defense subnet overlaps a route, interface, Docker or VPN network')
    if count!=1:
        raise ValueError('Defense subnet is missing or configured more than once')
    return True
