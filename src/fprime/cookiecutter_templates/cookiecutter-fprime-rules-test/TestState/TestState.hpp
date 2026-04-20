// ======================================================================
// \title  TestState.hpp
// \author chammard
// \brief  Shadow state model for RuleDemo rule-based testing
// ======================================================================

#ifndef {{cookiecutter.component_name}}_TestState_HPP
#define {{cookiecutter.component_name}}_TestState_HPP

#include <{{cookiecutter.__include_path_prefix}}{{cookiecutter.component_name}}/{{cookiecutter.component_name}}.hpp>

namespace RuleBasedTesting {

class {{cookiecutter.component_name}}TestState {
    //-----------------------------------------------------------------
    // State variables
    //-----------------------------------------------------------------
  public:
    FwSizeType m_toDo;
};

}  // namespace RuleBasedTesting

#endif
