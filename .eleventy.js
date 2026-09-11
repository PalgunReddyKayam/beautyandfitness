export default function (eleventyConfig) {
  eleventyConfig.addPassthroughCopy({ "src/assets": "assets" });
  eleventyConfig.addPassthroughCopy({ "src/admin": "admin" });
  eleventyConfig.addPassthroughCopy({ "src/uploads": "uploads" });
  eleventyConfig.addPassthroughCopy({ "_headers": "_headers" });

  eleventyConfig.addCollection("posts", (api) =>
    api.getFilteredByGlob("src/posts/*.md").filter(p => !p.data.draft).reverse()
  );
  eleventyConfig.addCollection("beauty", (api) =>
    api.getFilteredByGlob("src/posts/*.md").filter(p => !p.data.draft && p.data.pillar === "beauty").reverse()
  );
  eleventyConfig.addCollection("fitness", (api) =>
    api.getFilteredByGlob("src/posts/*.md").filter(p => !p.data.draft && p.data.pillar === "fitness").reverse()
  );

  eleventyConfig.addFilter("date", (d) =>
    new Date(d).toLocaleDateString("en-GB", { day: "numeric", month: "long", year: "numeric" })
  );
  eleventyConfig.addFilter("isoDate", (d) => new Date(d).toISOString());
  eleventyConfig.addFilter("readTime", (content) => {
    const words = (content || "").replace(/<[^>]+>/g, "").split(/\s+/).length;
    return Math.max(1, Math.round(words / 220)) + " min read";
  });
  eleventyConfig.addFilter("limit", (arr, n) => arr.slice(0, n));

  return {
    dir: { input: "src", output: "_site", includes: "_includes", data: "_data" },
    markdownTemplateEngine: "njk",
    htmlTemplateEngine: "njk",
  };
}
