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

function Loader() {
  return (
    <div className="flex justify-center items-center h-screen w-screen bg-white">
      <img
        src="https://thumbs.gfycat.com/HugeDeliciousArchaeocete-max-1mb.gif"
        alt="Test data"
        width={"auto"}
        height={"auto"}
      />
    </div>
  );
}

export default Loader;
