import "@testing-library/jest-dom/vitest";

// jsdom não implementa scrollIntoView
Element.prototype.scrollIntoView = () => {};
