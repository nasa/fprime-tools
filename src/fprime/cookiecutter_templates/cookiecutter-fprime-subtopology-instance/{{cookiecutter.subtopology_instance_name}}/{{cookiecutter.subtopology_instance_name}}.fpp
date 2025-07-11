module {{cookiecutter.subtopology_instance_name}} {
    constant BASE_ID = {{cookiecutter.base_id}}
    
    # Include the subtopology template from the specified path
    include "{{cookiecutter.subtopology_template_path}}/subtopology-template.fppi"
}
