{%- if cookiecutter.enable_logging == "yes" %}
#ifndef TLMLOGGERTEE_PINGENTRIES_HPP
#define TLMLOGGERTEE_PINGENTRIES_HPP

  namespace PingEntries {
    namespace TlmLoggerTee_comLog       {enum { WARN = 3, FATAL = 5 };}
  }

#endif
{%- endif %} 