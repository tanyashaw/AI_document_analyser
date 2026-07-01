function Sidebar({

  sidebarOpen,
  setSidebarOpen,

  sessions,

  activeSession,

  loadHistory,

  createNewSession,

  theme,

  setTheme

}) {

  return (

    <div
      className={`
      transition-all
      duration-300
      flex
      flex-col
      border-r

      ${
        sidebarOpen
          ? "w-72"
          : "w-20"
      }

      ${
        theme === "dark"
          ? "bg-slate-900 border-slate-800 text-white"
          : "bg-white border-slate-200 text-slate-800"
      }
      `}
    >

      <div className="p-4 flex justify-between items-center">

        {sidebarOpen && (

          <h2 className="font-bold text-lg">

            AI Document Intelligence

          </h2>

        )}

        <button
          onClick={() =>
            setSidebarOpen(
              !sidebarOpen
            )
          }
        >
          ☰
        </button>

      </div>

      <div className="px-4">

        <button

          onClick={createNewSession}

          className="
          w-full
          bg-indigo-600
          text-white
          py-2
          rounded-lg
          hover:bg-indigo-700
          "
        >

          + New Chat

        </button>

      </div>

      <div className="mt-6 px-3 flex-1 overflow-y-auto">

        {sidebarOpen && (

          <h3
            className="
            text-xs
            uppercase
            text-slate-400
            mb-3
            "
          >

            Recent Chats

          </h3>

        )}

        {

          sessions.map(
            (session) => (

              <button

                key={
                  session.session_id
                }

                onClick={() =>
                  loadHistory(
                    session.session_id
                  )
                }

                className={`
                w-full
                text-left
                px-3
                py-3
                rounded-lg
                mb-2

                ${
                  activeSession ===
                  session.session_id

                  ? "bg-indigo-100 text-indigo-700"

                  : "hover:bg-slate-100"
                }
                `}
              >

                {

                  sidebarOpen

                  ? session.title

                  : "💬"

                }

              </button>

            )
          )

        }

      </div>

      <div className="p-4 border-t">

        <button

          onClick={() =>

            setTheme(

              theme === "light"

              ? "dark"

              : "light"

            )

          }

          className="
          w-full
          py-2
          rounded-lg
          border
          "
        >

          {

            theme === "light"

            ? "🌙 Dark"

            : "☀️ Light"

          }

        </button>

      </div>

    </div>

  );

}

export default Sidebar;