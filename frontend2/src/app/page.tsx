// components
import { Navbar, Footer } from "@/components";

// sections
import Hero from "./hero";
import Posts from "./posts";

export default function Campaign() {
  return (
    <>
      <Navbar />
      <Hero />
      <Posts />
      <Footer />
    </>
  );
}
