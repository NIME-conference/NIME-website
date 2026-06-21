---
layout: page
title: Translated Works
permalink: /translations/
---

This page lists works in the NIME proceedings (Paper, Music, Installation, and alt.nime) that have been translated into other languages by their authors. The list is organised in reverse chronological order.

Translations are done independently by the authors. The original works were written, peer‑reviewed, and accepted in English. The English version should be regarded as the version of record (as stated in the disclaimer note shown above the translations).

Translations are stored exclusively in [Zenodo](https://zenodo.org/communities/nime_conference/). Each translated work has its own DOI and is presented in Zenodo as a “version of” the original English work, which has its own DOI. If you wish to cite a translated version, you may do so, but you should also cite the original English version.

For future NIME works, authors can submit translations (as separate PDF files, one per language, using the same template) together with the camera‑ready material.

For past and already published NIME works, authors should use the template (when available) from the relevant past NIME edition (see [Past NIMEs archived sites](/past-nimes/)) and send the translated paper to the [NIME Proceedings Officer](/board/) close to the next camera‑ready submission deadline. Translated papers are processed and published once a year together with the upcoming proceedings.

{% assign first_year = 2001 %}
{% assign current_year = "now" | date: "%Y" %}
{% assign nime_years = (first_year .. current_year) %}

{% for i in nime_years reversed %}

{% assign year_papers        = site.data.nime_papers        | where: "year", i | where_exp: "e", "e.translations" %}
{% assign year_music         = site.data.nime_music         | where: "year", i | where_exp: "e", "e.translations" %}
{% assign year_installations = site.data.nime_installations | where: "year", i | where_exp: "e", "e.translations" %}
{% assign year_alt           = site.data.nime_alt           | where: "year", i | where_exp: "e", "e.translations" %}

{% if year_papers != empty or year_music != empty or year_installations != empty or year_alt != empty %}
<h3>{{ i }}</h3>
{% endif %}

{% if year_papers != empty %}
<h4>Paper</h4>
<ul>
{% for entry in year_papers %}
{% capture original_url %}{{ entry.ID | datapage_url: "proc" | replace: ".html", "/index.html" | relative_url }}{% endcapture %}
{% assign tparts = entry.translations | split: ", " %}
{% assign tsize  = tparts | size %}
{% assign tlast  = tsize | minus: 1 %}

{% for idx in (0..tlast) %}
{% assign idx_mod_3 = idx | modulo: 3 %}
{% if idx_mod_3 == 0 %}
  {% assign lang        = tparts[idx] %}
  {% assign doi_index   = idx | plus: 1 %}
  {% assign title_index = idx | plus: 2 %}

  {% if doi_index < tsize %}
    {% assign tdoi = tparts[doi_index] %}
  {% else %}
    {% assign tdoi = "" %}
  {% endif %}

  {% if title_index < tsize %}
    {% assign ttitle = tparts[title_index] %}
  {% else %}
    {% assign ttitle = "" %}
  {% endif %}

  {% if tdoi != "" %}
<li>{% include author_names.html entry=entry %}. {{ entry.year }}. {% if ttitle != "" %}<a href="https://doi.org/{{ tdoi }}">{{ ttitle }}</a>.{% else %}<a href="https://doi.org/{{ tdoi }}">{{ lang }} translation</a>.{% endif %} {{ entry.booktitle }}. ({{ lang }} translation of <a href="{{ original_url }}">{{ entry.title }}</a>).</li>
  {% endif %}
{% endif %}
{% endfor %}
{% endfor %}
</ul>
{% endif %}

{% if year_music != empty %}
<h4>Music</h4>
<ul>
{% for entry in year_music %}
{% capture original_url %}{{ entry.ID | datapage_url: "proc_music" | replace: ".html", "/index.html" | relative_url }}{% endcapture %}
{% assign tparts = entry.translations | split: ", " %}
{% assign tsize  = tparts | size %}
{% assign tlast  = tsize | minus: 1 %}

{% for idx in (0..tlast) %}
{% assign idx_mod_3 = idx | modulo: 3 %}
{% if idx_mod_3 == 0 %}
  {% assign lang        = tparts[idx] %}
  {% assign doi_index   = idx | plus: 1 %}
  {% assign title_index = idx | plus: 2 %}

  {% if doi_index < tsize %}
    {% assign tdoi = tparts[doi_index] %}
  {% else %}
    {% assign tdoi = "" %}
  {% endif %}

  {% if title_index < tsize %}
    {% assign ttitle = tparts[title_index] %}
  {% else %}
    {% assign ttitle = "" %}
  {% endif %}

  {% if tdoi != "" %}
<li>{% include author_names.html entry=entry %}. {{ entry.year }}. {% if ttitle != "" %}<a href="https://doi.org/{{ tdoi }}">{{ ttitle }}</a>.{% else %}<a href="https://doi.org/{{ tdoi }}">{{ lang }} translation</a>.{% endif %} {{ entry.booktitle }}. ({{ lang }} translation of <a href="{{ original_url }}">{{ entry.title }}</a>).</li>
  {% endif %}
{% endif %}
{% endfor %}
{% endfor %}
</ul>
{% endif %}

{% if year_installations != empty %}
<h4>Installation</h4>
<ul>
{% for entry in year_installations %}
{% capture original_url %}{{ entry.ID | datapage_url: "proc_installations" | replace: ".html", "/index.html" | relative_url }}{% endcapture %}
{% assign tparts = entry.translations | split: ", " %}
{% assign tsize  = tparts | size %}
{% assign tlast  = tsize | minus: 1 %}

{% for idx in (0..tlast) %}
{% assign idx_mod_3 = idx | modulo: 3 %}
{% if idx_mod_3 == 0 %}
  {% assign lang        = tparts[idx] %}
  {% assign doi_index   = idx | plus: 1 %}
  {% assign title_index = idx | plus: 2 %}

  {% if doi_index < tsize %}
    {% assign tdoi = tparts[doi_index] %}
  {% else %}
    {% assign tdoi = "" %}
  {% endif %}

  {% if title_index < tsize %}
    {% assign ttitle = tparts[title_index] %}
  {% else %}
    {% assign ttitle = "" %}
  {% endif %}

  {% if tdoi != "" %}
<li>{% include author_names.html entry=entry %}. {{ entry.year }}. {% if ttitle != "" %}<a href="https://doi.org/{{ tdoi }}">{{ ttitle }}</a>.{% else %}<a href="https://doi.org/{{ tdoi }}">{{ lang }} translation</a>.{% endif %} {{ entry.booktitle }}. ({{ lang }} translation of <a href="{{ original_url }}">{{ entry.title }}</a>).</li>
  {% endif %}
{% endif %}
{% endfor %}
{% endfor %}
</ul>
{% endif %}

{% if year_alt != empty %}
<h4>alt.nime</h4>
<ul>
{% for entry in year_alt %}
{% capture original_url %}{{ entry.ID | datapage_url: "proc_alt" | replace: ".html", "/index.html" | relative_url }}{% endcapture %}
{% assign tparts = entry.translations | split: ", " %}
{% assign tsize  = tparts | size %}
{% assign tlast  = tsize | minus: 1 %}

{% for idx in (0..tlast) %}
{% assign idx_mod_3 = idx | modulo: 3 %}
{% if idx_mod_3 == 0 %}
  {% assign lang        = tparts[idx] %}
  {% assign doi_index   = idx | plus: 1 %}
  {% assign title_index = idx | plus: 2 %}

  {% if doi_index < tsize %}
    {% assign tdoi = tparts[doi_index] %}
  {% else %}
    {% assign tdoi = "" %}
  {% endif %}

  {% if title_index < tsize %}
    {% assign ttitle = tparts[title_index] %}
  {% else %}
    {% assign ttitle = "" %}
  {% endif %}

  {% if tdoi != "" %}
<li>{% include author_names.html entry=entry %}. {{ entry.year }}. {% if ttitle != "" %}<a href="https://doi.org/{{ tdoi }}">{{ ttitle }}</a>.{% else %}<a href="https://doi.org/{{ tdoi }}">{{ lang }} translation</a>.{% endif %} {{ entry.booktitle }}. ({{ lang }} translation of <a href="{{ original_url }}">{{ entry.title }}</a>).</li>
  {% endif %}
{% endif %}
{% endfor %}
{% endfor %}
</ul>
{% endif %}

{% endfor %}
