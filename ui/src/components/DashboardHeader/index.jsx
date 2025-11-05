/***
 * Copyright (2023) Hewlett Packard Enterprise Development LP
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * You may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 ***/


import React, { useState } from "react";
import { NavLink } from "react-router-dom";
import "./index.css";

function DashboardHeader() {
  const [toggleMenu, setToggleMenu] = useState(false);

  const navLinks = [
    { to: "/artifacts", label: "Artifacts" },
    { to: "/executions", label: "Executions" },
    { to: "/display_lineage", label: "Lineage" },
    { to: "/tensorboard", label: "TensorBoard" },
    { to: "/metahub", label: "Metahub" },
  ];

  return (
    <nav className="bg-white border-b border-gray-200 shadow-sm">
      <div className="w-full px-2">
        <div className="grid grid-cols-3 h-16 items-center w-full">
          {/* Left: Branding */}
          <div className="flex items-center pl-2 col-span-1">
            <NavLink
              to="/"
              className="font-bold text-2xl font-sans tracking-tight bg-teal-600 text-white px-4 py-2 rounded-lg shadow"
              style={{ textAlign: 'left' }}
            >
              CMF SERVER
            </NavLink>
          </div>
          {/* Center: NavLinks (desktop only) */}
          <div className="hidden lg:flex justify-center items-center col-span-1">
            <div className="flex space-x-6">
              {navLinks.map((link) => (
                <NavLink
                  key={link.to}
                  to={link.to}
                  className="text-xl text-gray-700 hover:text-teal-600 font-semibold font-sans transition-colors"
                  activeClassName="active"
                >
                  {link.label}
                </NavLink>
              ))}
              <a
                href="https://hewlettpackard.github.io/cmf/api/public/cmf/"
                target="_blank"
                rel="noreferrer"
                className="text-xl text-gray-700 hover:text-teal-600 font-semibold font-sans transition-colors whitespace-nowrap"
              >
                API Docs
              </a>
            </div>
          </div>
          {/* Right: Hamburger for mobile */}
          <div className="flex justify-end items-center col-span-1 lg:hidden">
            <button
              className="inline-flex items-center justify-center p-2 rounded-md text-teal-600 hover:text-white hover:bg-teal-600 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-teal-500"
              aria-label="Toggle navigation"
              onClick={() => setToggleMenu(!toggleMenu)}
            >
              <svg className="h-6 w-6" stroke="currentColor" fill="none" viewBox="0 0 24 24">
                {toggleMenu ? (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                ) : (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16M4 18h16" />
                )}
              </svg>
            </button>
          </div>
        </div>
      </div>
      {/* Mobile Sidebar */}
      <div className={`lg:hidden ${toggleMenu ? "block" : "hidden"}`}>
        <div className="px-2 pt-2 pb-3 space-y-1 bg-white border-t border-gray-200 shadow-md">
          {navLinks.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              className="block px-3 py-2 rounded-md text-xl font-medium font-sans text-gray-700 hover:bg-teal-600 hover:text-white transition-colors"
              activeClassName="active"
              onClick={() => setToggleMenu(false)}
            >
              {link.label}
            </NavLink>
          ))}
          <a
            href="https://hewlettpackard.github.io/cmf/api/public/cmf/"
            target="_blank"
            rel="noreferrer"
            className="block px-3 py-2 rounded-md text-xl font-medium font-sans text-gray-700 hover:bg-teal-600 hover:text-white transition-colors whitespace-nowrap"
            onClick={() => setToggleMenu(false)}
          >
            API Docs
          </a>
        </div>
      </div>
    </nav>
  );
}

export default DashboardHeader;
