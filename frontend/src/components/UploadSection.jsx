import { useState } from "react";

function UploadSection({

  file,

  setFile,

  textInput,

  setTextInput,

  handleUpload,

  handleTextSubmit,

  loading

}) {

  const [mode, setMode] =
    useState("pdf");

  return (

    <div
      className="
      bg-white
      rounded-2xl
      border
      p-6
      "
    >

      <h2
        className="
        text-xl
        font-bold
        mb-6
        "
      >

        Upload Source

      </h2>

      <div className="flex gap-6 mb-6">

        <label>

          <input

            type="radio"

            checked={
              mode === "pdf"
            }

            onChange={() =>
              setMode("pdf")
            }

          />

          <span className="ml-2">
            PDF
          </span>

        </label>

        <label>

          <input

            type="radio"

            checked={
              mode === "docx"
            }

            onChange={() =>
              setMode("docx")
            }

          />

          <span className="ml-2">
            DOCX
          </span>

        </label>

        <label>

          <input

            type="radio"

            checked={
              mode === "text"
            }

            onChange={() =>
              setMode("text")
            }

          />

          <span className="ml-2">
            Text
          </span>

        </label>

      </div>

      {mode === "pdf" && (

        <div>

          <input

            type="file"

            accept=".pdf"

            onChange={(e) =>
              setFile(
                e.target.files[0]
              )
            }

          />

          <button

            onClick={handleUpload}

            className="
            mt-4
            bg-indigo-600
            text-white
            px-4
            py-2
            rounded-lg
            "
          >

            Analyze PDF

          </button>

        </div>

      )}

      {mode === "docx" && (

        <div
          className="
          p-4
          bg-amber-50
          rounded-lg
          "
        >

          DOCX support coming soon

        </div>

      )}

      {mode === "text" && (

        <div>

          <textarea

            rows={8}

            value={textInput}

            onChange={(e) =>
              setTextInput(
                e.target.value
              )
            }

            className="
            w-full
            border
            rounded-lg
            p-3
            "
          />

          <button

            onClick={
              handleTextSubmit
            }

            className="
            mt-4
            bg-indigo-600
            text-white
            px-4
            py-2
            rounded-lg
            "
          >

            Analyze Text

          </button>

        </div>

      )}

      {loading && (

        <p className="mt-4">

          Processing...

        </p>

      )}

    </div>

  );

}

export default UploadSection;