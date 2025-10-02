const eleventyNavigationPlugin = require("@11ty/eleventy-navigation");
const pluginTOC = require('eleventy-plugin-toc');
const markdownItAnchor = require("markdown-it-anchor");
const markdownItReplaceLink = require("markdown-it-replace-link");

module.exports = function(eleventyConfig) {
  // Add navigation plugin
  eleventyConfig.addPlugin(eleventyNavigationPlugin);

  // Add TOC plugin
  eleventyConfig.addPlugin(pluginTOC, {
    tags: ['h2', 'h3', 'h4'],
    ul: true,
    wrapper: 'nav'
  });

  // Configure markdown-it with anchor support and link replacement
  eleventyConfig.amendLibrary("md", mdLib => {
    mdLib.set({ html: true, linkify: true, typographer: true });

    // Add anchor support for headings
    mdLib.use(markdownItAnchor, {
      permalink: markdownItAnchor.permalink.linkInsideHeader({
        symbol: '#',
        placement: 'before'
      }),
      level: [2, 3, 4]
    });

    // Replace .md links with proper HTML paths
    mdLib.use(markdownItReplaceLink, {
      replaceLink: function (link, env) {
        // Skip external links, anchors only, and non-.md links
        if (link.startsWith('http://') ||
            link.startsWith('https://') ||
            link.startsWith('#') ||
            !link.includes('.md')) {
          return link;
        }

        // Remove .md extension and add trailing slash for clean URLs
        // Handles both:
        // - ./architecture/index.md -> ./architecture/index/
        // - application-environment-api.md#anchor -> application-environment-api/#anchor
        return link.replace(/\.md(#|$)/, '/$1');
      }
    });
  });

  // Set default layout for markdown files
  eleventyConfig.addGlobalData("layout", "base.html");

  // Copy assets to output
  eleventyConfig.addPassthroughCopy("assets");
  eleventyConfig.addPassthroughCopy("diagrams");

  // Watch for changes
  eleventyConfig.addWatchTarget("./ADR/");
  eleventyConfig.addWatchTarget("./architecture/");
  eleventyConfig.addWatchTarget("./ref/");

  // Disable gitignore usage so we can process generated files like ADR/index.md
  eleventyConfig.setUseGitIgnore(false);

  return {
    dir: {
      input: ".",
      output: "_site",
      includes: "_includes",
      layouts: "_layouts",
      data: "_data"
    },
    templateFormats: ["md", "html", "njk"],
    markdownTemplateEngine: false, // Don't process Markdown with Nunjucks to avoid conflicts with {{ }} syntax
    htmlTemplateEngine: "njk"
  };
};
