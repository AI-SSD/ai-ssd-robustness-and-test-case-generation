#include <stdio.h>
#include <stdlib.h>
#include <errno.h>
#include <support/check.h>

static int do_test(void)
{
    char user[] = "username"; // Replace with a valid username if available
    gid_t group = 1000;       // Replace with a valid group ID if available
    gid_t groups[32];
    int ngroups = sizeof(groups) / sizeof(gid_t);

    TEST_COMPARE(getgrouplist(user, group, groups, &ngroups), -1);
    TEST_VERIFY(errno == ENOENT); // User does not exist

    errno = 0;
    ngroups = sizeof(groups) / sizeof(gid_t);
    TEST_COMPARE(getgrouplist(NULL, group, NULL, &ngroups), -1);
    TEST_VERIFY(errno == EFAULT);

    errno = 0;
    groups[0] = 1; // Valid group ID
    ngroups = 1;
    TEST_COMPARE(getgrouplist(user, group, groups, &ngroups), 1); // User and group match
    TEST_VERIFY(groups[0] == 1);
    TEST_VERIFY(ngroups == 1);

    errno = 0;
    groups[0] = 2; // Invalid group ID
    ngroups = 1;
    TEST_COMPARE(getgrouplist(user, group, groups, &ngroups), -1);
    TEST_VERIFY(errno == ESRCH); // Group does not exist

    errno = 0;
    groups[0] = 1000; // Valid group ID
    ngroups = 1;
    groups[1] = 2000; // Invalid group ID
    TEST_COMPARE(getgrouplist(user, group, groups, &ngroups), -1);
    TEST_VERIFY(errno == ESRCH); // Second group does not exist

    errno = 0;
    groups[0] = 1; // Valid group ID
    ngroups = 2;
    groups[1] = 2; // Invalid group ID
    TEST_COMPARE(getgrouplist(user, group, groups, &ngroups), -1);
    TEST_VERIFY(errno == ESRCH); // Second group does not exist

    errno = 0;
    groups[0] = 1; // Valid group ID
    ngroups = 32;
    groups[1] = 2; // Invalid group ID
    TEST_COMPARE(getgrouplist(user, group, groups, &ngroups), -1);
    TEST_VERIFY(errno == ESRCH); // Second group does not exist

    return 0;
}

#include <support/test-driver.c>