import "./globals.css";
import type { Metadata } from "next";
import { Roboto } from "next/font/google";
import { Navbar, Footer } from "@/components";

import { AuthProvider } from "@/contexts/AuthContext";

const roboto = Roboto({
  subsets: ["latin"],
  weight: ["300", "400", "500", "700", "900"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "MCP Server Hub",
  description:
  ""
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <link
          rel="stylesheet"
          href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.2.1/css/all.min.css"
          integrity="sha512-MV7K8+y+gLIBoVD59lQIYicR65iaqukzvf/nwasF0nqhPay5w/9lJmVM2hMDcnK1OnMGCdVK+iQrJ7lzPJQd1w=="
          crossOrigin="anonymous"
          referrerPolicy="no-referrer"
        />
        <link rel="icon" href="/favicon.svg" type="image/svg+xml" />
      </head>
      <body className={roboto.className}>
        <AuthProvider>
          <Navbar />
          {children}
          <Footer />
  
        </AuthProvider>
      </body>
    </html>
  );
}
