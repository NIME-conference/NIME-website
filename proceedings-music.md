---
layout: page
title: Music Proceedings
permalink: /music/
---

This page lists all peer-reviewed Music performed at NIME conferences, organized in reverse chronological order. (Note: This list is incomplete, as we are in the process of assembling proceedings of Music from previous NIME conferences.) At times, Music proceedings are included with the Paper proceedings.

<!-- This liquid code sets up a list of years up to now (this year) and generates lists of bib entries for each year. Empty years are not listed. -->
{% assign first_year = 2001 %}
{% assign current_year = "now" | date: "%Y" %}
{% assign nime_years = (first_year .. current_year) %}
{% for i in nime_years reversed %}

{% assign year_entries = site.data.nime_music | where: "year", i %}
{% unless year_entries == empty %}
<h3>{{ i }}</h3>

<ul>
{% for entry in year_entries %}
{% capture entry_url %}{{ entry.ID | datapage_url: "proc_music" | replace: ".html", "/index.html" | relative_url }}{% endcapture %}
<li>{% include citation.html entry=entry link=entry_url %}</li>
{% endfor %}
</ul>
{% endunless %}
{% endfor %}


{% comment %}
{% bibliography --file nime_music %}
{% endcomment %}

<script>
// map our commands to the classList methods
const fnmap = {
  'toggle': 'toggle',
    'show': 'add',
    'hide': 'remove'
};
const collapse = (selector, cmd) => {
  const targets = Array.from(document.querySelectorAll(selector));
  targets.forEach(target => {
    target.classList[fnmap[cmd]]('show');
  });
}

// Grab all the trigger elements on the page
const triggers = Array.from(document.querySelectorAll('[data-toggle="collapse"]'));
// Listen for click events, but only on our triggers
window.addEventListener('click', (ev) => {
  const elm = ev.target;
  if (triggers.includes(elm)) {
    const selector = elm.getAttribute('data-target');
    collapse(selector, 'toggle');
  }
}, false);
</script>
