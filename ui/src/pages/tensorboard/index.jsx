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

import DashboardHeader from "../../components/DashboardHeader";
import Footer from "../../components/Footer";

const TensorBoard = () => {
  const TB_PATH = "/tensorboard/"; // same-origin path exposed by NGINX

  return (
    <>
      <section
        className="flex flex-col bg-white min-h-screen"
      >
        <DashboardHeader />
        <div className="flex flex-row">
          <div className="container justify-center items-center mx-auto px-4">
            <iframe
              title="Tensorboard"
              src={TB_PATH}
              allowFullScreen
              width="100%"
              height="1200"
            />
          </div>
        </div>
        <Footer />
      </section>
    </>
  );
};

export default TensorBoard;
