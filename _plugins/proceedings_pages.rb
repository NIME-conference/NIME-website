# frozen_string_literal: true

# Generates one HTML page per bibliography entry (papers, music, installations,
# alt.nime), plus the Liquid filter the listing pages use to link to them and
# the Liquid tag that writes the redirects into .htaccess.
#
# Where a page lands depends on its year (see `proceedings_pages` in _config.yml):
#
#   * Years listed under `moved_years` get their page next to the PDF, in the
#     folder the hand-uploaded proceedings live in:
#         /proceedings/<year>/<id>.html        (e.g. /proceedings/2026/nime2026_1.html)
#     Google Scholar asks for the abstract page and the PDF to be in the same
#     subdirectory (#89). The old page URL is redirected there with a 301.
#
#   * Every other year keeps the historical layout:
#         /<legacy_dir>/<id>/                  (e.g. /proc/nime2001_cook/)
#
# The build only ever ADDS .html files to /proceedings/<year>/. The deploy
# rsync runs without --delete, so nothing uploaded by hand is touched (#65).
# scripts/check_site_quality.py checks both of these after every build.
#
# <id> is the entry's BibTeX ID, transliterated to ASCII and lowercased exactly
# as the jekyll-datapage-generator plugin used to do it, so no existing URL
# changes for the years that have not moved.

module NIME
  module ProceedingsPages
    LAYOUT = "paper"

    # Transliteration tables from jekyll-datapage-generator 1.4.0
    # (c) 2014-2020 Adolfo Villafiorita, MIT License. Kept verbatim so that
    # page names stay identical to the ones that plugin produced.
    TR_FROM = "ÀÁÂÃÄÅàáâãäåĀāĂăĄąÇçĆćĈĉĊċČčÐðĎďĐđÈÉÊËèéêëĒēĔĕĖėĘęĚěĜĝĞğĠġĢģĤĥĦħÌÍÎÏìíîïĨĩĪīĬĭĮįİıĴĵĶķĸĹĺĻļĽľĿŀŁłÑñŃńŅņŇňŉŊŋÑñÒÓÔÕÖØòóôõöøŌōŎŏŐőŔŕŖŗŘřŚśŜŝŞşŠšſŢţŤťŦŧÙÚÛÜùúûüŨũŪūŬŭŮůŰűŲųŴŵÝýÿŶŷŸŹźŻżŽž"
    TR_TO   = "AAAAAAaaaaaaAaAaAaCcCcCcCcCcDdDdDdEEEEeeeeEeEeEeEeEeGgGgGgGgHhHhIIIIiiiiIiIiIiIiIiJjKkkLlLlLlLlLlNnNnNnNnnNnNnOOOOOOooooooOoOoOoRrRrRrSsSsSsSssTtTtTtUUUUuuuuUuUuUuUuUuUuWwYyyYyYZzZzZz"

    module_function

    # The file/folder name for an entry, from its BibTeX ID.
    def page_name(id)
      id.to_s.tr(TR_FROM, TR_TO).downcase.strip.gsub(" ", "-").gsub(/[^\w.-]/, "")
    end

    def config(site)
      site.config["proceedings_pages"] || {}
    end

    def moved_years(site)
      Array(config(site)["moved_years"]).map(&:to_i)
    end

    def moved?(site, entry)
      moved_years(site).include?(entry["year"].to_i)
    end

    # URL of the page in the historical location, e.g. /proc/nime2001_cook/
    def legacy_url(entry, legacy_dir)
      "/#{legacy_dir}/#{page_name(entry['ID'])}/"
    end

    # URL of the page next to its PDF, e.g. /proceedings/2026/nime2026_1.html
    def moved_url(entry)
      "/proceedings/#{entry['year'].to_i}/#{page_name(entry['ID'])}.html"
    end

    def url(site, entry, legacy_dir)
      moved?(site, entry) ? moved_url(entry) : legacy_url(entry, legacy_dir)
    end

    # Yields [entry, legacy_dir] for every entry in every configured data set.
    def each_entry(site)
      Array(config(site)["sets"]).each do |set|
        records = site.data[set["data"]]
        unless records
          Jekyll.logger.error "ProceedingsPages:", "no data file for '#{set['data']}'; skipping"
          next
        end
        records.each { |entry| yield entry, set["legacy_dir"] }
      end
    end

    class Page < Jekyll::Page
      def initialize(site, entry, permalink)
        @site = site
        @base = site.source
        @dir  = File.dirname(permalink)
        @name = permalink.end_with?("/") ? "index.html" : File.basename(permalink)
        process(@name)
        self.content = ""
        @data = {
          "layout"    => LAYOUT,
          "title"     => entry["title"] || entry["ID"],
          "permalink" => permalink,
          "entry"     => entry,
        }
        Jekyll::Hooks.trigger :pages, :post_init, self
      end
    end

    class Generator < Jekyll::Generator
      safe true
      priority :normal

      def generate(site)
        unless site.layouts.key?(LAYOUT)
          Jekyll.logger.error "ProceedingsPages:", "layout '#{LAYOUT}' not found; no entry pages generated"
          return
        end
        seen = {}
        ProceedingsPages.each_entry(site) do |entry, legacy_dir|
          unless entry["ID"]
            Jekyll.logger.warn "ProceedingsPages:", "entry without an ID skipped: #{entry['title'].inspect}"
            next
          end
          permalink = ProceedingsPages.url(site, entry, legacy_dir)
          if seen[permalink]
            Jekyll.logger.warn "ProceedingsPages:", "#{permalink} generated twice (#{seen[permalink]} and #{entry['ID']}); keeping the first"
            next
          end
          seen[permalink] = entry["ID"]
          site.pages << Page.new(site, entry, permalink)
        end
        Jekyll.logger.info "ProceedingsPages:", "#{seen.size} entry pages, " \
          "#{seen.keys.count { |u| u.start_with?('/proceedings/') }} of them next to their PDFs " \
          "(moved_years: #{ProceedingsPages.moved_years(site).join(', ')})"
      end
    end

    # {{ entry | proceedings_page_url: "proc" }} -> the page's URL for the entry.
    module Filters
      def proceedings_page_url(entry, legacy_dir)
        ProceedingsPages.url(@context.registers[:site], entry, legacy_dir)
      end
    end

    # {% proceedings_redirects %} -> one RewriteRule per moved entry, sending its
    # old /<legacy_dir>/<id>/ URL to the new page with a 301. Used in .htaccess.
    class RedirectsTag < Liquid::Tag
      def render(context)
        site = context.registers[:site]
        rules = []
        ProceedingsPages.each_entry(site) do |entry, legacy_dir|
          next unless entry["ID"] && ProceedingsPages.moved?(site, entry)
          from = ProceedingsPages.legacy_url(entry, legacy_dir)
          to   = ProceedingsPages.moved_url(entry)
          # Matches /proc/<id>, /proc/<id>/ and /proc/<id>/index.html.
          rules << "RewriteRule ^#{Regexp.escape(from[1..-2])}(/|/index\\.html)?$ #{site.config['url']}#{to} [R=301,L,NC]"
        end
        rules.join("\n")
      end
    end
  end
end

Liquid::Template.register_filter(NIME::ProceedingsPages::Filters)
Liquid::Template.register_tag("proceedings_redirects", NIME::ProceedingsPages::RedirectsTag)
