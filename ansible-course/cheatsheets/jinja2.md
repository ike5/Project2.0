# Jinja2 Templating Cheatsheet

Ansible uses **Jinja2** in templates (`.j2`) and in playbook expressions.

## The three delimiters
```jinja
{{ expression }}      {# output a value #}
{% statement %}       {# logic: if/for/set #}
{# comment #}         {# not rendered #}
```

## Variables & filters
```jinja
{{ http_port }}                     {# a variable #}
{{ user.name }}                     {# nested #}
{{ items[0] }}                      {# index #}
{{ name | upper }}                  {# filters with | #}
{{ port | default(80) }}            {# fallback if undefined #}
{{ path | basename }}               {# /a/b/c -> c #}
{{ list | join(', ') }}             {# join a list #}
{{ list | length }}
{{ text | replace('a','b') }}
{{ value | int }}   {{ value | bool }}
{{ data | to_nice_json }}  {{ data | to_nice_yaml }}
{{ secret | password_hash('sha512') }}
{{ ansible_default_ipv4.address }}  {# a fact #}
```

## Conditionals
```jinja
{% if env == "prod" %}
worker_processes auto;
{% elif env == "staging" %}
worker_processes 2;
{% else %}
worker_processes 1;
{% endif %}
```

## Loops
```jinja
upstream app {
{% for host in groups['app'] %}
    server {{ hostvars[host].ansible_default_ipv4.address }}:8080;
{% endfor %}
}
```
- `groups['app']` — hosts in the `app` inventory group.
- `hostvars[host]` — another host's variables/facts (great for building configs that
  reference peers, e.g. a load balancer listing its backends).

## Whitespace control
```jinja
{%- if x %}...{%- endif %}   {# the '-' trims surrounding whitespace/newlines #}
```

## Useful facts (from the `setup` module)
```jinja
{{ ansible_hostname }}
{{ ansible_distribution }} {{ ansible_distribution_version }}
{{ ansible_os_family }}                 {# Debian / RedHat #}
{{ ansible_default_ipv4.address }}
{{ ansible_processor_vcpus }}
{{ ansible_memtotal_mb }}
```

## In playbooks (not just templates)
```yaml
when: ansible_os_family == "Debian"
when: http_port | int > 1024
msg: "Deploying {{ app_version | default('latest') }} to {{ inventory_hostname }}"
loop: "{{ packages }}"
```

## A template example (nginx)
`templates/site.conf.j2`:
```jinja
server {
    listen {{ http_port | default(80) }} default_server;
    server_name {{ server_name | default(ansible_hostname) }};
    root {{ web_root }};
    index index.html;
{% if enable_gzip | default(true) %}
    gzip on;
{% endif %}
}
```
Rendered with the `template` module:
```yaml
- ansible.builtin.template:
    src: site.conf.j2
    dest: /etc/nginx/sites-available/site
  notify: Reload nginx
```
