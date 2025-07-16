{%- if cookiecutter.enable_logging == "yes" %}
#ifndef EVENTLOGGERTEE_PINGENTRIES_HPP
#define EVENTLOGGERTEE_PINGENTRIES_HPP

  namespace PingEntries {
    namespace EventLoggerTee_comLog       {enum { WARN = 3, FATAL = 5 };}
  }

#endif
{%- endif %} 