/***
 * Copyright (2025) Hewlett Packard Enterprise Development LP
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

const Highlight = ({ text, highlight }) => {
    // If the highlight text is empty or contains only whitespace, return the original text
    if (!highlight.trim()) {
        return <span>{text}</span>;
    }

    // Create a regular expression to match the highlight text, case insensitive
    const regex = new RegExp(`(${highlight})`, 'gi');
    // Split the text into parts based on the highlight text
    const parts = text.split(regex);

    return (
        <span>
            {parts.map((part, index) =>
                // If the part matches the highlight text, wrap it in a mark element
                regex.test(part) ? (
                    <mark key={index} className="bg-yellow-300 text-black">
                        {part}
                    </mark>
                ) : (
                    part
                )
            )}
        </span>
    );
};

export default Highlight;