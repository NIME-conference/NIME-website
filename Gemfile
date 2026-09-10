source "https://rubygems.org"

# The site is built in GitHub Actions and rsynced to our own server, so it
# does not need the github-pages gem (which forces Jekyll into safe mode and
# disables _plugins). Depend on Jekyll and the plugins we use directly.
gem "jekyll", "~> 4.3"

group :jekyll_plugins do
  gem "jekyll-datapage-generator"   # one page per bibliography entry
  gem "jekyll-feed"                 # /feed.xml
  gem "jekyll-seo-tag"              # {% seo %}
  gem "jekyll-sitemap"              # /sitemap.xml
  gem "jekyll-toc"                  # toc_only filter
end

gem "kramdown-parser-gfm"           # GitHub-flavoured markdown, as before

# Windows does not include zoneinfo files, so bundle the tzinfo-data gem
gem "tzinfo-data", platforms: [:windows, :jruby]

# Needed by `jekyll serve` on Ruby 3
gem "webrick", "~> 1.7"
