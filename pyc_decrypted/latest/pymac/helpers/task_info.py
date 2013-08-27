#Embedded file name: pymac/helpers/task_info.py
from ctypes import sizeof, byref, addressof
from ..constants import KERN_SUCCESS, TASK_BASIC_INFO, THREAD_BASIC_INFO
from ..dlls import libc
from ..types import integer_t, mach_msg_type_number_t, natural_t, task_basic_info, task_flavor_t, task_info_t, task_port_t, thread_basic_info, thread_info_t
TASK_BASIC_INFO_COUNT = sizeof(task_basic_info) / sizeof(natural_t)

def get_basic_task_info(pid):
    task = task_port_t()
    if libc.task_for_pid(libc.mach_task_self(), pid, byref(task)) != KERN_SUCCESS:
        raise Exception('Failure')
    tasks_info = task_basic_info()
    info_count = mach_msg_type_number_t(TASK_BASIC_INFO_COUNT)
    try:
        if libc.task_info(task, task_flavor_t(TASK_BASIC_INFO), task_info_t(integer_t.from_address(addressof(tasks_info))), byref(info_count)) != KERN_SUCCESS:
            raise Exception('Failure')
    finally:
        libc.mach_port_deallocate(libc.mach_task_self(), task)

    return tasks_info


THREAD_BASIC_INFO_COUNT = sizeof(thread_basic_info) / sizeof(natural_t)

def get_basic_thread_info():
    info = thread_basic_info()
    info_count = mach_msg_type_number_t(THREAD_BASIC_INFO_COUNT)
    ret = libc.thread_info(libc.mach_thread_self(), task_flavor_t(THREAD_BASIC_INFO), thread_info_t(integer_t.from_address(addressof(info))), byref(info_count))
    if ret != KERN_SUCCESS:
        raise Exception('Failure %d' % ret)
    return info


def get_cpu_timer():
    info = thread_basic_info()
    info_count = mach_msg_type_number_t(THREAD_BASIC_INFO_COUNT)
    flavor = task_flavor_t(THREAD_BASIC_INFO)
    info_t = thread_info_t(integer_t.from_address(addressof(info)))
    info_count_t = byref(info_count)

    def timer(close = False):
        ret = libc.thread_info(libc.mach_thread_self(), flavor, info_t, info_count_t)
        if ret != KERN_SUCCESS:
            raise Exception('Failure in thread %d -> %d' % (libc.mach_thread_self(), ret))
        return info.user_time.seconds + info.system_time.seconds + (info.user_time.microseconds + info.system_time.microseconds) / 1000000.0

    return timer
