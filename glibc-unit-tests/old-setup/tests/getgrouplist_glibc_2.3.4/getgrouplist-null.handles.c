#include <stdio.h>
#include <stdlib.h>
#include <errno.h>
#include <support/check.h>

static int do_test(void)
{
    char *user = NULL;
    gid_t group = 1000;       // Replace with a valid group ID if available
    gid_t groups[32];
    int ngroups = sizeof(groups) / sizeof(gid_t);

    TEST_COMPARE(getgrouplist(user, group, groups, &ngroups), -1);
    TEST_VERIFY(errno == EFAULT);

    errno = 0;
    user = "username"; // Replace with a valid username if available
    groups[0] = 1; // Valid group ID
    ngroups = 1;
    TEST_COMPARE(getgrouplist(user, group, groups, &ngroups), 1); // User and group match
    TEST_VERIFY(groups[0] == 1);
    TEST_VERIFY(ngroups == 1);

    errno = 0;
    user = "username"; // Replace with a valid username if available
    groups[0] = 2; // Invalid group ID
    ngroups = 1;
    TEST_COMPARE(getgrouplist(user, group, groups, &ngroups), -1);
    TEST_VERIFY(errno == ESRCH); // Group does not exist

    return 0;
}

#include <support/test-driver.c>