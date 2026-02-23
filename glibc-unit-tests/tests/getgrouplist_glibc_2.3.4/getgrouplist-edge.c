#include <stdio.h>
#include <stdlib.h>
#include <errno.h>
#include <support/check.h>

static int do_test(void)
{
    char user[] = "username"; // Replace with a valid username if available
    gid_t group = 0;       // Invalid group ID
    gid_t groups[32];
    int ngroups = sizeof(groups) / sizeof(gid_t);

    errno = 0;
    ngroups = 1;
    TEST_COMPARE(getgrouplist(user, group, groups, &ngroups), -1);
    TEST_VERIFY(errno == EINVAL); // Group ID is invalid

    return 0;
}

#include <support/test-driver.c>