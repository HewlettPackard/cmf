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

import React from "react";

function Footer() {
  return (
    <footer className={"text-center p-4 bg-black mt-auto text-white"}>
      <div>
        © 2023 Copyright
        <a
          className="text-white ml-5"
          href="https://github.com/HewlettPackard/cmf"
        >
          HPE Github
        </a>
      </div>
    </footer>
  );
}

export default Footer;
