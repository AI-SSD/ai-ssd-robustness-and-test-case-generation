nt
internal_function
__gconv_translit_find (struct trans_struct *trans)
{
  /* Transliteration module loading has been removed because it never
     worked as intended and suffered from a security vulnerability.
     Consequently, this function always fails.  */
  return 1;
}