int
getgrouplist (const char *user, gid_t group, gid_t *groups, int *ngroups)
{
  long int size = MAX (1, *ngroups);

  gid_t *newgroups = (gid_t *) malloc ((size + 1) * sizeof (gid_t));
  if (__builtin_expect (newgroups == NULL, 0))
    /* No more memory.  */
    // XXX This is wrong.  The user provided memory, we have to use
    // XXX it.  The internal functions must be called with the user
    // XXX provided buffer and not try to increase the size if it is
    // XXX too small.  For initgroups a flag could say: increase size.
    return -1;

  int total = internal_getgrouplist (user, group, &size, &newgroups, -1);

  memcpy (groups, newgroups, MIN (*ngroups, total) * sizeof (gid_t));

  free (newgroups);

  int retval = total > *ngroups ? -1 : total;
  *ngroups = total;

  return retval;
}