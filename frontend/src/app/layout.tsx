import "./globals.css";

export const metadata = {
  title: "EDSea PLUR Planner",
  description: "AI-powered schedule builder for sailing the electric seas.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-gray-50 text-gray-900 antialiased">
        {children}
      </body>
    </html>
  );
}