function Dashboard({ result }) {

  if (!result) return null;

  return (

    <div className="space-y-4">

      <div className="bg-white rounded-xl shadow p-4">

        <h3 className="font-bold mb-2">
          Project Scope
        </h3>

        <ul className="list-disc ml-5">

          {result.final_extracted_data.project_scope.map(
            (item, index) => (
              <li key={index}>{item}</li>
            )
          )}

        </ul>

      </div>

      <div className="bg-white rounded-xl shadow p-4">

        <h3 className="font-bold mb-2">
          Deadlines
        </h3>

        <ul className="list-disc ml-5">

          {result.final_extracted_data.deadlines.map(
            (item, index) => (
              <li key={index}>{item}</li>
            )
          )}

        </ul>

      </div>

      <div className="bg-white rounded-xl shadow p-4">

        <h3 className="font-bold mb-2">
          Compliance
        </h3>

        <ul className="list-disc ml-5">

          {result.final_extracted_data.compliance_requirements.map(
            (item, index) => (
              <li key={index}>{item}</li>
            )
          )}

        </ul>

      </div>

    </div>

  );
}

export default Dashboard;