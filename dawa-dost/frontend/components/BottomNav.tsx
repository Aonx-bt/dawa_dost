"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const ITEMS = [
  { href: "/", label: "Home", icon: "🏠" },
  { href: "/medications", label: "Meds", icon: "💊" },
  { href: "/progress", label: "Progress", icon: "📈" },
  { href: "/calls", label: "Calls", icon: "📞" },
  { href: "/profile", label: "Profile", icon: "👤" },
];

export function BottomNav() {
  const pathname = usePathname();

  return (
    <nav className="fixed inset-x-0 bottom-0 z-20 border-t border-slate-100 bg-white/95 backdrop-blur">
      <div className="mx-auto flex max-w-md items-stretch justify-between px-2 py-1.5">
        {ITEMS.map((item) => {
          const active = item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex flex-1 flex-col items-center gap-0.5 rounded-xl px-2 py-1.5 text-xs font-medium transition ${
                active ? "text-teal-700" : "text-slate-400"
              }`}
            >
              <span className={`text-lg ${active ? "" : "opacity-70"}`}>{item.icon}</span>
              {item.label}
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
