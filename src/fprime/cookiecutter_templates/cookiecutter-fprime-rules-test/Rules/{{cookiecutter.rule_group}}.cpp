// ======================================================================
// \title  {{cookiecutter.rule_group}}.cpp
// \author chammard
// \brief  Rule implementations for {{cookiecutter.rule_group}} checks
// ======================================================================

#include <{{cookiecutter.__include_path_prefix}}{{cookiecutter.component_name}}/{{cookiecutter.component_name}}.hpp>
#include "RuleBasedTesting/{{cookiecutter.component_name}}/test/ut/{{cookiecutter.component_name}}Tester.hpp"

namespace RuleBasedTesting {

bool {{cookiecutter.component_name}}Tester::{{cookiecutter.rule_group}}__TodoRule__precondition() const {
    return true;
}

void {{cookiecutter.component_name}}Tester::{{cookiecutter.rule_group}}__TodoRule__action() {
}

}  // namespace RuleBasedTesting
