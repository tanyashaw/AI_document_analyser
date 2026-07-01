import ReactMarkdown from "react-markdown";

function ChatWindow({

  messages,

  question,

  setQuestion,

  handleAsk

}) {

  return (

    <div
      className="
      flex
      flex-col
      h-full
      "
    >

      <div
        className="
        flex-1
        overflow-y-auto
        p-4
        space-y-4
        "
      >

        {messages.map(
          (message, index) => (

            <div
              key={index}
              className={
                message.role === "user"
                  ? `
                    ml-auto
                    bg-blue-100
                    rounded-xl
                    p-3
                    max-w-[75%]
                  `
                  : `
                    bg-gray-100
                    rounded-xl
                    p-3
                    max-w-[75%]
                  `
              }
            >

              <ReactMarkdown>

                {message.content}

              </ReactMarkdown>

            </div>

          )
        )}

      </div>

      <div
        className="
        border-t
        p-4
        flex
        gap-3
        "
      >

        <input
          type="text"
          value={question}
          onChange={(e) =>
            setQuestion(
              e.target.value
            )
          }
          placeholder="Ask about the document..."
          className="
          flex-1
          border
          p-3
          rounded-lg
          "
        />

        <button
          onClick={handleAsk}
          className="
          bg-green-600
          text-white
          px-6
          rounded-lg
          "
        >
          Ask
        </button>

      </div>

    </div>

  );
}

export default ChatWindow;