import { useEffect, useRef, useState } from "react";
import type { SearchEntry } from "../buildSearchIndex";
import { searchGeographies } from "../buildSearchIndex";
import { dashboardContent } from "../content/dashboard";

interface Props {
  index: SearchEntry[];
  selectedKeys: Set<string>;
  onSelect: (entry: SearchEntry) => void;
}

export function GeoSearchBar({ index, selectedKeys, onSelect }: Props) {
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);
  const [highlight, setHighlight] = useState(0);
  const wrapRef = useRef<HTMLDivElement>(null);

  const results = searchGeographies(query, index);

  useEffect(() => {
    setHighlight(0);
  }, [query]);

  useEffect(() => {
    function onDocClick(e: MouseEvent) {
      if (wrapRef.current && !wrapRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", onDocClick);
    return () => document.removeEventListener("mousedown", onDocClick);
  }, []);

  function pick(entry: SearchEntry) {
    onSelect(entry);
    setQuery("");
    setOpen(false);
  }

  function onKeyDown(e: React.KeyboardEvent) {
    if (!open || results.length === 0) return;
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setHighlight((h) => Math.min(h + 1, results.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setHighlight((h) => Math.max(h - 1, 0));
    } else if (e.key === "Enter" && results[highlight]) {
      e.preventDefault();
      pick(results[highlight]);
    } else if (e.key === "Escape") {
      setOpen(false);
    }
  }

  return (
    <div className="geo-search" ref={wrapRef}>
      <label className="sr-only" htmlFor="geo-search-input">
        {dashboardContent.searchPlaceholder}
      </label>
      <input
        id="geo-search-input"
        type="search"
        className="geo-search-input"
        placeholder={dashboardContent.searchPlaceholder}
        value={query}
        autoComplete="off"
        onChange={(e) => {
          setQuery(e.target.value);
          setOpen(true);
        }}
        onFocus={() => setOpen(true)}
        onKeyDown={onKeyDown}
      />
      {open && query.trim() && results.length > 0 && (
        <ul className="geo-search-results" role="listbox">
          {results.map((entry, i) => {
            const already = selectedKeys.has(entry.key);
            return (
              <li key={entry.key}>
                <button
                  type="button"
                  role="option"
                  aria-selected={i === highlight}
                  className={`geo-search-option${i === highlight ? " is-highlighted" : ""}`}
                  disabled={already}
                  onMouseEnter={() => setHighlight(i)}
                  onClick={() => pick(entry)}
                >
                  <span className="geo-search-name">{entry.name}</span>
                  <span className="geo-search-level">
                    {entry.level === "county" ? "County" : "Place / CDP"}
                  </span>
                  {already && <span className="geo-search-added">Added</span>}
                </button>
              </li>
            );
          })}
        </ul>
      )}
      {open && query.trim() && results.length === 0 && (
        <div className="geo-search-empty">No matching counties or places.</div>
      )}
    </div>
  );
}
