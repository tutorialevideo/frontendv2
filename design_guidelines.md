{
  "brand": {
    "name": "mFirme",
    "positioning": [
      "Premium Romanian company intelligence database",
      "Search-first, fast, trustworthy",
      "Financial Times editorial restraint + modern SaaS clarity"
    ],
    "design_personality": {
      "keywords": [
        "authoritative",
        "calm",
        "precise",
        "airy",
        "data-forward",
        "quietly premium"
      ],
      "anti_goals": [
        "no cluttered directory look",
        "no loud badges everywhere",
        "no aggressive paywall/lock spam",
        "no heavy gradients",
        "no center-aligned reading layouts"
      ]
    }
  },

  "global_layout": {
    "container": {
      "max_width": "max-w-7xl",
      "page_padding": "px-4 sm:px-6 lg:px-8",
      "vertical_rhythm": "py-6 sm:py-8 lg:py-10",
      "desktop_first_note": "Desktop gets a 2-column search layout; mobile collapses filters into a Drawer."
    },
    "grid_system": {
      "base": "12-col mental model",
      "homepage": "Hero search centered within content column but page remains left-aligned; supporting stats in 3–4 cards grid.",
      "search_results": "Left filters (3 cols) + results (9 cols) on lg; stacked on mobile.",
      "company_profile": "Header summary row + Tabs; inside tabs use 2-col grids for key/value blocks and tables for financials.",
      "category_pages": "Header + breadcrumb + list; optional right rail for ‘Top in category’ on xl."
    },
    "navigation": {
      "top_nav": "Sticky, thin (h-14) with subtle bottom border; includes logo, main links, and a compact search trigger.",
      "breadcrumbs": "Always present on results, category, and company pages; use shadcn Breadcrumb.",
      "footer": "Editorial style: 2–3 columns, small type, no gradients."
    }
  },

  "typography": {
    "font_pairing": {
      "headings": {
        "family": "Space Grotesk",
        "google_font": "https://fonts.google.com/specimen/Space+Grotesk",
        "usage": "H1/H2, card titles, KPI numbers"
      },
      "body": {
        "family": "IBM Plex Sans",
        "google_font": "https://fonts.google.com/specimen/IBM+Plex+Sans",
        "usage": "Body, tables, filters, helper text"
      },
      "mono_optional": {
        "family": "IBM Plex Mono",
        "usage": "CAEN codes, CUI, registration numbers"
      }
    },
    "scale_tailwind": {
      "h1": "text-4xl sm:text-5xl lg:text-6xl font-semibold tracking-tight",
      "h2": "text-base md:text-lg text-muted-foreground",
      "section_title": "text-lg sm:text-xl font-semibold tracking-tight",
      "card_title": "text-sm sm:text-base font-semibold",
      "body": "text-sm sm:text-base leading-6",
      "small": "text-xs sm:text-sm text-muted-foreground"
    },
    "editorial_rules": [
      "Prefer sentence case for headings (not ALL CAPS).",
      "Numbers: use tabular-nums for financial tables and KPIs.",
      "Line length: keep long descriptions to max-w-prose."
    ]
  },

  "color_system": {
    "notes": [
      "Navy/blue trust palette with warm neutral surfaces.",
      "Avoid saturated gradients; use solid surfaces + subtle tints.",
      "Use accent sparingly for CTAs and highlights."
    ],
    "tokens_css_custom_properties": {
      "where": "/app/frontend/src/index.css (replace :root and .dark tokens)",
      "light": {
        "--background": "210 33% 99%",
        "--foreground": "222 47% 11%",
        "--card": "0 0% 100%",
        "--card-foreground": "222 47% 11%",
        "--popover": "0 0% 100%",
        "--popover-foreground": "222 47% 11%",

        "--primary": "221 72% 32%",
        "--primary-foreground": "210 40% 98%",

        "--secondary": "214 32% 96%",
        "--secondary-foreground": "222 47% 11%",

        "--muted": "214 32% 96%",
        "--muted-foreground": "215 16% 40%",

        "--accent": "204 94% 94%",
        "--accent-foreground": "221 72% 28%",

        "--border": "214 20% 90%",
        "--input": "214 20% 90%",
        "--ring": "221 72% 45%",

        "--destructive": "0 72% 52%",
        "--destructive-foreground": "210 40% 98%",

        "--radius": "0.75rem",

        "--chart-1": "221 72% 40%",
        "--chart-2": "199 89% 40%",
        "--chart-3": "160 60% 35%",
        "--chart-4": "43 90% 55%",
        "--chart-5": "0 72% 52%"
      },
      "dark_optional": {
        "--background": "222 47% 7%",
        "--foreground": "210 40% 98%",
        "--card": "222 47% 9%",
        "--card-foreground": "210 40% 98%",
        "--popover": "222 47% 9%",
        "--popover-foreground": "210 40% 98%",

        "--primary": "204 94% 60%",
        "--primary-foreground": "222 47% 11%",

        "--secondary": "222 30% 14%",
        "--secondary-foreground": "210 40% 98%",

        "--muted": "222 30% 14%",
        "--muted-foreground": "215 20% 70%",

        "--accent": "221 72% 18%",
        "--accent-foreground": "204 94% 70%",

        "--border": "222 30% 18%",
        "--input": "222 30% 18%",
        "--ring": "204 94% 60%",

        "--destructive": "0 62% 40%",
        "--destructive-foreground": "210 40% 98%"
      }
    },
    "semantic_usage": {
      "page_bg": "bg-background",
      "surface": "bg-card",
      "surface_muted": "bg-secondary",
      "text_primary": "text-foreground",
      "text_secondary": "text-muted-foreground",
      "borders": "border-border",
      "focus": "focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background"
    },
    "accent_color": {
      "name": "Sky ink",
      "use_cases": [
        "autocomplete highlight",
        "active filter chips",
        "small KPI deltas",
        "links hover underline"
      ],
      "tailwind_hint": "Use token-based colors; avoid hardcoded blues except for charts."
    }
  },

  "texture_and_background": {
    "rule": "Use subtle noise/texture overlays to avoid flatness; keep it extremely low contrast.",
    "implementation": {
      "hero_bg": "Use a mild diagonal tint overlay (not a strong gradient) + optional noise.",
      "css_snippet": "Add a pseudo-element on hero wrapper: after:absolute after:inset-0 after:bg-[radial-gradient(60%_60%_at_20%_10%,hsl(var(--accent)/0.55),transparent_60%),radial-gradient(50%_50%_at_80%_0%,hsl(var(--primary)/0.10),transparent_55%)] after:pointer-events-none"
    },
    "image_noise_urls": [
      {
        "category": "subtle_texture",
        "description": "Optional background texture for hero or empty states (use opacity 0.04–0.07).",
        "url": "https://images.unsplash.com/photo-1582035100994-9ddfc34b1dae?crop=entropy&cs=srgb&fm=jpg&ixlib=rb-4.1.0&q=85"
      }
    ]
  },

  "components": {
    "component_path": {
      "shadcn_primary": "/app/frontend/src/components/ui/",
      "use_these": [
        "button.jsx",
        "input.jsx",
        "command.jsx (autocomplete)",
        "badge.jsx",
        "card.jsx",
        "tabs.jsx",
        "table.jsx",
        "breadcrumb.jsx",
        "pagination.jsx",
        "sheet.jsx (mobile filters)",
        "drawer.jsx (mobile quick actions)",
        "skeleton.jsx",
        "tooltip.jsx",
        "hover-card.jsx",
        "select.jsx",
        "slider.jsx",
        "calendar.jsx (if date filters are added)",
        "separator.jsx",
        "scroll-area.jsx",
        "sonner.jsx (toasts)"
      ]
    },

    "header_nav": {
      "layout": "Left: logo + primary nav; Right: compact search + pricing/login.",
      "styles": {
        "wrapper": "sticky top-0 z-40 bg-background/80 backdrop-blur supports-[backdrop-filter]:bg-background/60 border-b border-border",
        "inner": "h-14 flex items-center justify-between",
        "logo": "font-semibold tracking-tight",
        "nav_link": "text-sm text-muted-foreground hover:text-foreground transition-colors",
        "active_link": "text-foreground"
      },
      "data_testids": {
        "logo": "header-logo-link",
        "search_trigger": "header-search-trigger",
        "pricing_link": "header-pricing-link"
      }
    },

    "homepage_hero_search": {
      "goal": "Search-first: the search bar is the product.",
      "layout": "Hero with H1 + short H2 + large search input + suggestion chips + trust stats row.",
      "search_component": {
        "use": "Command (shadcn) as autocomplete container + Input styling",
        "structure": [
          "Command",
          "CommandInput",
          "CommandList",
          "CommandItem"
        ],
        "styles": {
          "shell": "relative",
          "input": "h-14 sm:h-16 text-base sm:text-lg pl-12 pr-4 rounded-xl border border-border bg-card shadow-sm focus-visible:ring-2 focus-visible:ring-ring",
          "icon": "absolute left-4 top-1/2 -translate-y-1/2 text-muted-foreground",
          "dropdown": "mt-2 rounded-xl border border-border bg-popover shadow-lg overflow-hidden"
        },
        "micro_interactions": [
          "On focus: show dropdown with recent searches (if any) + top categories.",
          "On typing: highlight matched substring with accent background (bg-accent).",
          "On select: route to company profile or results page; show subtle loading bar/skeleton."
        ],
        "data_testids": {
          "hero_search_input": "home-hero-search-input",
          "hero_search_suggestion_item": "home-hero-search-suggestion-item"
        }
      },
      "trust_row": {
        "use": "Card or simple inline stats",
        "kpis": [
          "144,286+ companies",
          "Updated daily",
          "CAEN coverage",
          "Financial snapshots"
        ],
        "styles": "grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4 mt-6"
      }
    },

    "search_results_page": {
      "layout": {
        "desktop": "Filters sidebar (sticky) + results list",
        "mobile": "Filters in Sheet; results full width"
      },
      "filters": {
        "components": [
          "Select (județ/localitate)",
          "Input (CAEN code)",
          "Slider (revenue/employees)",
          "Checkbox (active only, VAT payer, etc.)",
          "Badge chips for active filters"
        ],
        "styles": {
          "sidebar": "lg:sticky lg:top-20 lg:h-[calc(100vh-5rem)] lg:overflow-auto pr-2",
          "section_title": "text-xs font-semibold tracking-wide text-muted-foreground uppercase",
          "chip": "rounded-full px-3 py-1 text-xs bg-secondary text-foreground border border-border"
        },
        "data_testids": {
          "open_filters_button": "search-open-filters-button",
          "filters_sidebar": "search-filters-sidebar",
          "apply_filters_button": "search-apply-filters-button",
          "clear_filters_button": "search-clear-filters-button"
        }
      },
      "results_list": {
        "result_card": {
          "use": "Card",
          "layout": "Left: company name + locality; Right: key metrics + CTA",
          "styles": {
            "card": "rounded-xl border border-border bg-card hover:shadow-md transition-shadow",
            "title": "text-base font-semibold",
            "meta": "text-xs text-muted-foreground",
            "kpi_row": "mt-3 grid grid-cols-2 sm:grid-cols-4 gap-2",
            "kpi": "text-xs",
            "kpi_value": "font-semibold tabular-nums",
            "cta": "mt-3 flex items-center gap-2"
          },
          "micro_interactions": [
            "Hover: elevate shadow only (no transform).",
            "On click: show skeleton on next page; preserve scroll position when back.",
            "Keyboard: entire card is focusable with visible ring."
          ],
          "data_testids": {
            "result_card": "search-result-company-card",
            "result_card_open": "search-result-open-company-button"
          }
        },
        "empty_state": {
          "tone": "Helpful, not apologetic.",
          "content": "Suggest removing filters + show popular categories.",
          "use": "Card + Button + Badge"
        },
        "loading": {
          "use": "Skeleton",
          "pattern": "Render 8–12 skeleton cards; keep layout stable."
        }
      },
      "pagination": {
        "use": "Pagination (shadcn)",
        "data_testids": {
          "pagination": "search-results-pagination",
          "pagination-next": "search-results-pagination-next",
          "pagination-prev": "search-results-pagination-prev"
        }
      }
    },

    "company_profile_page": {
      "header_summary": {
        "layout": "Company name + badges (status) + key identifiers + primary actions.",
        "components": ["Badge", "Button", "Tooltip"],
        "styles": {
          "wrapper": "rounded-2xl border border-border bg-card p-5 sm:p-6",
          "title": "text-2xl sm:text-3xl font-semibold tracking-tight",
          "submeta": "mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-muted-foreground",
          "actions": "mt-4 flex flex-wrap items-center gap-2"
        },
        "data_testids": {
          "company-title": "company-profile-title",
          "company-cui": "company-profile-cui",
          "company-caen": "company-profile-caen",
          "company-share": "company-profile-share-button"
        }
      },
      "tabs": {
        "use": "Tabs (shadcn)",
        "tabs_list": ["Overview", "Financials", "Juridic", "Contact", "Similar"],
        "styles": {
          "tabs_list": "bg-secondary rounded-xl p-1",
          "tab": "text-sm",
          "tab_active": "bg-card shadow-sm"
        },
        "data_testids": {
          "tabs": "company-profile-tabs",
          "tab-overview": "company-profile-tab-overview",
          "tab-financials": "company-profile-tab-financials"
        }
      },
      "financials": {
        "use": "Table + small KPI cards",
        "kpi_cards": "grid grid-cols-2 lg:grid-cols-4 gap-3",
        "table": {
          "styles": "rounded-xl border border-border overflow-hidden",
          "numbers": "tabular-nums text-right"
        },
        "charting_optional": {
          "library": "recharts",
          "why": "Lightweight trend lines for revenue/profit over years.",
          "install": "npm i recharts",
          "usage_note": "Use 1–2 line charts max; keep axes subtle; no gradients in chart fills."
        }
      },
      "premium_masking": {
        "principle": "Mask elegantly; show value shape; offer upgrade as a calm inline CTA.",
        "patterns": [
          {
            "name": "Partial mask",
            "example": "074*** ***",
            "use_for": "phone, email"
          },
          {
            "name": "Blur overlay",
            "example": "Ion P****",
            "use_for": "admin names"
          }
        ],
        "ui": {
          "masked_field": "inline-flex items-center gap-2 rounded-lg border border-border bg-secondary px-3 py-2",
          "blur_text": "[filter:blur(6px)] select-none",
          "upgrade_link": "text-sm font-medium text-primary hover:underline"
        },
        "micro_interactions": [
          "Hover on masked field: show Tooltip explaining ‘Available on Premium’.",
          "Click upgrade: open Dialog with plan comparison (not full page redirect)."
        ],
        "data_testids": {
          "masked-phone": "company-profile-masked-phone",
          "masked-admin": "company-profile-masked-admin",
          "upgrade-cta": "company-profile-upgrade-cta"
        }
      },
      "similar_companies": {
        "use": "Card list + small badges",
        "layout": "2-col on md, 3-col on xl",
        "data_testids": {
          "similar-companies-section": "company-profile-similar-companies"
        }
      }
    },

    "category_pages": {
      "types": ["/judet/[slug]", "/localitate/[slug]", "/caen/[code]"],
      "layout": "Breadcrumb + editorial header + stats strip + list/table toggle.",
      "list_table_toggle": {
        "use": "ToggleGroup",
        "data_testids": {
          "view-toggle": "category-view-toggle"
        }
      },
      "seo_header": {
        "style": "Like an editorial deck: title + 1–2 sentence description + key stats.",
        "max_width": "max-w-3xl"
      }
    },

    "pricing_page": {
      "tone": "Calm, transparent, enterprise-like.",
      "layout": "3 plan cards + comparison table.",
      "components": ["Card", "Table", "Button", "Badge"],
      "cta": "Primary CTA uses solid primary; secondary is outline; no gradients.",
      "data_testids": {
        "pricing-plan-card": "pricing-plan-card",
        "pricing-primary-cta": "pricing-primary-cta"
      }
    }
  },

  "motion_and_microinteractions": {
    "principles": [
      "Motion should communicate state change (loading, expand, filter applied).",
      "Prefer opacity + shadow transitions; avoid layout-jank transforms.",
      "Respect prefers-reduced-motion."
    ],
    "recommended_library": {
      "name": "framer-motion",
      "install": "npm i framer-motion",
      "use_cases": [
        "Results list fade-in on new query",
        "Filter chips animate in/out",
        "Dialog/Sheet entrance polish"
      ],
      "default_transition": "{ type: 'spring', stiffness: 260, damping: 26 }"
    },
    "tailwind_utilities": {
      "hover": "transition-colors duration-150",
      "shadow": "transition-shadow duration-200",
      "focus": "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
    }
  },

  "seo_and_content_design": {
    "meta": {
      "title_pattern": "{Entity} — mFirme",
      "description_pattern": "Short, factual, keyword-rich; avoid hype.",
      "open_graph": "Use a consistent OG image template (solid background + logo + entity name)."
    },
    "structured_data": {
      "company_profile": "JSON-LD Organization where possible; include address, identifier, sameAs if available.",
      "category_pages": "ItemList for company listings; BreadcrumbList for breadcrumbs."
    },
    "content_hierarchy": [
      "Always show: company name, status, locality, CAEN, CUI.",
      "Then: revenue/employees (if available), last update.",
      "Then: premium-only fields with elegant masking."
    ]
  },

  "accessibility": {
    "requirements": [
      "WCAG AA contrast for text and interactive elements.",
      "All interactive elements must be reachable by keyboard.",
      "Use focus-visible rings; never remove outline without replacement.",
      "Tables: use proper headers; keep row hover subtle."
    ],
    "reduced_motion": "Wrap motion with prefers-reduced-motion checks; keep essential state changes visible without animation."
  },

  "image_urls": {
    "hero_support": [
      {
        "category": "hero",
        "description": "Optional right-side hero visual (desktop only): modern corporate facade; keep opacity low and add blur.",
        "url": "https://images.pexels.com/photos/5504689/pexels-photo-5504689.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=650&w=940"
      }
    ],
    "category_headers": [
      {
        "category": "category-header",
        "description": "Use as subtle banner image for county/locality pages; apply grayscale + opacity 0.12.",
        "url": "https://images.unsplash.com/photo-1599398766380-23b3144142c7?crop=entropy&cs=srgb&fm=jpg&ixlib=rb-4.1.0&q=85"
      }
    ]
  },

  "implementation_notes_for_js": {
    "react_files": "Project uses .js (not .tsx). Keep components in JS, use PropTypes only if already used; otherwise rely on runtime checks.",
    "data_testid_rule": "Add data-testid to: search inputs, suggestion items, filter controls, result cards, pagination, tabs, premium CTAs, and any critical info fields.",
    "avoid_existing_css_pitfall": "Remove/ignore App.css default centering and dark header styles; rely on Tailwind + tokenized shadcn theme in index.css."
  },

  "instructions_to_main_agent": [
    "Update /app/frontend/src/index.css tokens to the provided navy/sky system; keep shadcn structure intact.",
    "Do NOT use App.css centered header styles; ensure .App is not text-align:center.",
    "Homepage: implement Command-based autocomplete search as the primary hero element; add skeletons for suggestion loading.",
    "Search results: desktop sticky filters sidebar; mobile filters in Sheet; results as Card list with KPI mini-grid.",
    "Company profile: header summary Card + Tabs; financials in Table + optional Recharts line chart; premium fields use partial mask/blur with calm upgrade Dialog.",
    "Add Breadcrumb on all deep pages; ensure SEO-friendly headings and structured data hooks.",
    "Add Framer Motion for subtle entrance/exit of chips and results; respect reduced motion.",
    "Ensure every interactive and key informational element includes stable data-testid attributes (kebab-case)."
  ],

  "GENERAL_UI_UX_DESIGN_GUIDELINES": "- You must **not** apply universal transition. Eg: `transition: all`. This results in breaking transforms. Always add transitions for specific interactive elements like button, input excluding transforms\n- You must **not** center align the app container, ie do not add `.App { text-align: center; }` in the css file. This disrupts the human natural reading flow of text\n- NEVER: use AI assistant Emoji characters like`🤖🧠💭💡🔮🎯📚🎭🎬🎪🎉🎊🎁🎀🎂🍰🎈🎨🎰💰💵💳🏦💎🪙💸🤑📊📈📉💹🔢🏆🥇 etc for icons. Always use **FontAwesome cdn** or **lucid-react** library already installed in the package.json\n\n **GRADIENT RESTRICTION RULE**\nNEVER use dark/saturated gradient combos (e.g., purple/pink) on any UI element.  Prohibited gradients: blue-500 to purple 600, purple 500 to pink-500, green-500 to blue-500, red to pink etc\nNEVER use dark gradients for logo, testimonial, footer etc\nNEVER let gradients cover more than 20% of the viewport.\nNEVER apply gradients to text-heavy content or reading areas.\nNEVER use gradients on small UI elements (<100px width).\nNEVER stack multiple gradient layers in the same viewport.\n\n**ENFORCEMENT RULE:**\n    • Id gradient area exceeds 20% of viewport OR affects readability, **THEN** use solid colors\n\n**How and where to use:**\n   • Section backgrounds (not content backgrounds)\n   • Hero section header content. Eg: dark to light to dark color\n   • Decorative overlays and accent elements only\n   • Hero section with 2-3 mild color\n   • Gradients creation can be done for any angle say horizontal, vertical or diagonal\n\n- For AI chat, voice application, **do not use purple color. Use color like light green, ocean blue, peach orange etc**\n\n</Font Guidelines>\n\n- Every interaction needs micro-animations - hover states, transitions, parallax effects, and entrance animations. Static = dead. \n   \n- Use 2-3x more spacing than feels comfortable. Cramped designs look cheap.\n\n- Subtle grain textures, noise overlays, custom cursors, selection states, and loading animations: separates good from extraordinary.\n   \n- Before generating UI, infer the visual style from the problem statement (palette, contrast, mood, motion) and immediately instantiate it by setting global design tokens (primary, secondary/accent, background, foreground, ring, state colors), rather than relying on any library defaults. Don't make the background dark as a default step, always understand problem first and define colors accordingly\n    Eg: - if it implies playful/energetic, choose a colorful scheme\n           - if it implies monochrome/minimal, choose a black–white/neutral scheme\n\n**Component Reuse:**\n\t- Prioritize using pre-existing components from src/components/ui when applicable\n\t- Create new components that match the style and conventions of existing components when needed\n\t- Examine existing components to understand the project's component patterns before creating new ones\n\n**IMPORTANT**: Do not use HTML based component like dropdown, calendar, toast etc. You **MUST** always use `/app/frontend/src/components/ui/ ` only as a primary components as these are modern and stylish component\n\n**Best Practices:**\n\t- Use Shadcn/UI as the primary component library for consistency and accessibility\n\t- Import path: ./components/[component-name]\n\n**Export Conventions:**\n\t- Components MUST use named exports (export const ComponentName = ...)\n\t- Pages MUST use default exports (export default function PageName() {...})\n\n**Toasts:**\n  - Use `sonner` for toasts\"\n  - Sonner component are located in `/app/src/components/ui/sonner.tsx`\n\nUse 2–4 color gradients, subtle textures/noise overlays, or CSS-based noise to avoid flat visuals."
}
