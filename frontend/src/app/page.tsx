"use client";

import { useState } from "react";
// components
// sections
import Hero from "./hero";
import Posts from "./posts";

export default function Campaign() {
  const [searchTerm, setSearchTerm] = useState("");

  const handleSearch = (term: string) => {
    setSearchTerm(term);
  };

  return (
    <>
      <Hero onSearch={handleSearch} />
      <Posts searchTerm={searchTerm} />
    </>
  );
}
