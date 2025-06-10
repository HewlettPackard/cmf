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
  // STATE WHICH WE WILL USE TO TOGGLE THE MENU ON HAMBURGER BUTTON PRESS
  const [toggleMenu, setToggleMenu] = useState(false);

  let displayButton;

  return (
    <nav className="flex items-center justify-between flex-wrap p-4 border-b border-gray-200 mb-1">
      <div className="flex items-center flex-shrink-0 mr-6 ">
        <NavLink
          to="/"
          className="cmf-server font-semibold text-2xl tracking-tight"
          activeClassName="active"
        >
          CMF SERVER
        </NavLink>
      </div>
      <div className="block lg:hidden">
        <button
          className="flex items-center px-3 py-2 border rounded text-black border-teal-400 hover:text-white hover:border-white"
          onClick={() => setToggleMenu(!toggleMenu)}
        >
          <svg
            className="fill-current h-3 w-3"
            viewBox="0 0 20 20"
            xmlns="http://www.w3.org/2000/svg"
          >
            <title>Menu</title>
            <path d="M0 3h20v2H0V3zm0 6h20v2H0V9zm0 6h20v2H0v-2z" />
          </svg>
        </button>
      </div>
      <div
        className={`animate-fade-in-down w-full ${
          toggleMenu ? "block" : "hidden"
        } flex-grow lg:flex lg:items-center lg:w-auto`}
      >
        <div className="text-xl font-semibold lg:flex-grow">
          <NavLink
            to="/artifacts"
            className="metadata block mt-4 lg:inline-block lg:mt-0 mx-4"
            activeClassName="active"
          >
            Artifacts
          </NavLink>
          <NavLink
            to="/executions"
            className="metadata block mt-4 lg:inline-block lg:mt-0  mx-4"
            activeClassName="active"
          >
            Executions
          </NavLink>
          <NavLink
            to="/display_lineage"
            className="metadata block mt-4 lg:inline-block lg:mt-0 mx-4"
            activeClassName="active"
          >
            Lineage
          </NavLink>
          <NavLink
            to="/tensorboard"
            className="metadata block mt-4 lg:inline-block lg:mt-0  mx-4"
            activeClassName="active"
          >
            TensorBoard
          </NavLink>
          <NavLink
            to="/metahub"
            className="metadata block mt-4 lg:inline-block lg:mt-0  mx-4"
            activeClassName="active"
          >
            Metahub
          </NavLink>
          <a
            href={"https://hewlettpackard.github.io/cmf/api/public/cmf/"}
            target={"_blank"}
            rel={"noreferrer"}
            className="metadata block mt-4 lg:inline-block lg:mt-0 text-slate-200 hover:text-white mx-4"
          >
            API Docs
          </a>
        </div>
        <div>
          <p>{displayButton}</p>
        </div>
      </div>
    </nav>
  );
}

export default DashboardHeader;
