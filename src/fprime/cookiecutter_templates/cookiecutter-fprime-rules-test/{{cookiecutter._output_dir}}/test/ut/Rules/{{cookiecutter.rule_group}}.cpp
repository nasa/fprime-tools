// ======================================================================
// \title  {{cookiecutter.__include_path_prefix}}/{{cookiecutter.rule_group}}.cpp
// \brief  Rule implementations for {{cookiecutter.rule_group}} checks
// ======================================================================

#include <{{cookiecutter.__include_path_prefix}}/{{cookiecutter._component_name}}.hpp>
#include "{{cookiecutter.__include_path_prefix}}/test/ut/{{cookiecutter._component_name}}Tester.hpp"

namespace {{cookiecutter._component_namespace}} {

bool {{cookiecutter._component_name}}Tester::{{cookiecutter.rule_group}}__TodoRule__precondition() const {
    return true;
}

void {{cookiecutter._component_name}}Tester::{{cookiecutter.rule_group}}__TodoRule__action() {
}


} // namespace {{cookiecutter._component_namespace}}
