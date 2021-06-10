# {{cookiecutter.component_name}} Component

## 1. Introduction

{{cookiecutter.component_short_description}}

## 2. Requirements

The requirements for `{{cookiecutter.component_namespace}}::{{cookiecutter.component_slug}}{{cookiecutter.component_explicit_component_suffix}}{{cookiecutter.component_impl_suffix}}` are as follows:

*Note:* Requirements are usually labelled with the initials of the component class, e.g. `CookieCutter -> CC-001`.

Requirement | Description | Verification Method
----------- | ----------- | -------------------
CC-001 | The `{{cookiecutter.component_namespace}}::{{cookiecutter.component_slug}}{{cookiecutter.component_explicit_component_suffix}}{{cookiecutter.component_impl_suffix}}` component acknowledge ping requests | Unit Test
CC-002 | The `{{cookiecutter.component_namespace}}::{{cookiecutter.component_slug}}{{cookiecutter.component_explicit_component_suffix}}{{cookiecutter.component_impl_suffix}}` component shall save the widgets | Unit Test

## 3. Design

### 3.1 Context

#### 3.1.1 Component Diagram

The `{{cookiecutter.component_namespace}}::{{cookiecutter.component_slug}}{{cookiecutter.component_explicit_component_suffix}}{{cookiecutter.component_impl_suffix}}` component has the following component diagram:

![`{{cookiecutter.component_namespace}}::{{cookiecutter.component_slug}}{{cookiecutter.component_explicit_component_suffix}}{{cookiecutter.component_impl_suffix}}` Diagram](img/{{cookiecutter.component_slug}}{{cookiecutter.component_explicit_component_suffix}}{{cookiecutter.component_impl_suffix}}BDD.jpg "{{cookiecutter.component_namespace}}::{{cookiecutter.component_slug}}{{cookiecutter.component_explicit_component_suffix}}{{cookiecutter.component_impl_suffix}}")

#### 3.1.2 Ports

The `{{cookiecutter.component_namespace}}::{{cookiecutter.component_slug}}{{cookiecutter.component_explicit_component_suffix}}{{cookiecutter.component_impl_suffix}}` component uses the following port types:

Port Data Type | Name | Direction | Kind | Usage
-------------- | ---- | --------- | ---- | -----
[`Svc::Fatal`](../Fatal/docs/sdd.html) | FatalReceive | Input | Synch | Receive FATAL notifications

### 3.2 Functional Description

(Lorum Ipsum) For Unix variants, it delays for one second before exiting with a segmentation fault. This allows time for the FATAL to propagate to the ground system so the user can see what event occurred and also generates a core for debugging (assuming ulimit is set correctly). For VxWorks, it suspends the calling thread. Projects can replace this component with another that does project-specific behavior like resets.

### 3.3 Scenarios

#### 3.3.1 FATAL Notification

The `{{cookiecutter.component_namespace}}::{{cookiecutter.component_slug}}{{cookiecutter.component_explicit_component_suffix}}{{cookiecutter.component_impl_suffix}}` handles FATAL notifications:

![FATAL Notification](img/FatalNotification.jpg)

### 3.4 State

`{{cookiecutter.component_namespace}}::{{cookiecutter.component_slug}}{{cookiecutter.component_explicit_component_suffix}}{{cookiecutter.component_impl_suffix}}` has no state machines (or does it?).

### 3.5 Algorithms

`{{cookiecutter.component_namespace}}::{{cookiecutter.component_slug}}{{cookiecutter.component_explicit_component_suffix}}{{cookiecutter.component_impl_suffix}}` has no significant algorithms.

## 4. Dictionary

Dictionaries: [HTML]({{cookiecutter.component_slug}}{{cookiecutter.component_explicit_component_suffix}}{{cookiecutter.component_impl_suffix}}.html) [MD]({{cookiecutter.component_slug}}.md)

## 4. Module Checklists

Document            | Link
------------------- | ----
Design Checklist    | [Link](Checklist_Design.xlsx)
Code Checklist      | [Link](Checklist_Code.xlsx)
Unit Test Checklist | [Link](Checklist_Unit_Test.xls)

## 5. Unit Testing

[Unit Test Output](../test/ut/output/test.txt)

[Coverage Summary](../test/ut/output/{{cookiecutter.component_namespace}}{{cookiecutter.component_slug}}{{cookiecutter.component_explicit_component_suffix}}{{cookiecutter.component_impl_suffix}}_gcov.txt)

[Coverage Output - `{{cookiecutter.component_namespace}}::{{cookiecutter.component_slug}}{{cookiecutter.component_explicit_component_suffix}}{{cookiecutter.component_impl_suffix}}.cpp`](../test/ut/output/{{cookiecutter.component_slug}}{{cookiecutter.component_explicit_component_suffix}}{{cookiecutter.component_impl_suffix}}.cpp.gcov)

[Coverage Output - `{{cookiecutter.component_slug}}ComponentAc.cpp`](../test/ut/output/{{cookiecutter.component_slug}}ComponentAc.cpp.gcov)

## 6. Change Log

Date       | Description
---------- | -----------
<TODAY> | Initial Component Design



