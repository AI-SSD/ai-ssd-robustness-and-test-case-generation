#include <stdio.h>
#include <stdlib.h>
#include <errno.h>
#include <support/check.h>

static int do_test(void)
{
    char user[] = "username"; // Replace with a valid username if available
    gid_t group = 1000;       // Replace with a valid group ID if available
    gid_t groups[32];
    int ngroups = 0;

    TEST_COMPARE(getgrouplist(user, group, NULL, &ngroups), -1);
    TEST_VERIFY(errno == EFAULT);

    errno = 0;
    ngroups = 1;
    groups[0] = 1; // Valid group ID
    TEST_COMPARE(getgrouplist(user, group, groups, &ngroups), 1); // User and group match
    TEST_VERIFY(groups[0] == 1);
    TEST_VERIFY(ngroups == 1);

    errno = 0;
    ngroups = 32;
    TEST_COMPARE(getgrouplist(user, group, groups, &ngroups), -1);
    TEST_VERIFY(errno == EFAULT);

    return 0;
}

#include <support/test-driver.c>