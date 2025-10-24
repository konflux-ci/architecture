module.exports = {
  permalink: function(data) {
    // If the page's input path starts with ./architecture/
    // strip that prefix from the output permalink
    if (data.page.inputPath.startsWith('./architecture/')) {
      // Get the path after ./architecture/
      let path = data.page.inputPath.substring('./architecture/'.length);

      // Handle index.md specially - map to root
      if (path === 'index.md') {
        return '/index.html';
      }

      // For other files, remove .md extension and add /index.html for clean URLs
      path = path.replace(/\.md$/, '/index.html');

      return '/' + path;
    }

    // For all other files, use default behavior
    return data.permalink;
  }
};
