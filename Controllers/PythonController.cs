using Microsoft.AspNetCore.Mvc;
using System.Diagnostics;
using System.Threading.Tasks;
using System.Text.Json;
using AnalysisNeuralNetwork.Data;
using Microsoft.EntityFrameworkCore;
using System.IO;

namespace AnalysisNeuralNetwork.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    public class PythonController : ControllerBase
    {
        private readonly ApplicationDbContext _context;
        private readonly JsonSerializerOptions jsonOptions = new JsonSerializerOptions
        {
            Encoder = System.Text.Encodings.Web.JavaScriptEncoder.UnsafeRelaxedJsonEscaping,
            WriteIndented = true
        };

        public PythonController(ApplicationDbContext context)
        {
            _context = context;
        }

        [HttpPost("run")]
        public async Task<IActionResult> RunPythonScript([FromBody] PythonScriptRequest request)
        {
            var scriptDirectory = Path.Combine(Directory.GetCurrentDirectory(), "NeuralNetwork");
            var tempJsonPath = Path.Combine(scriptDirectory, "temp_request.json");

            // Сериализуем запрос в временный JSON-файл
            var jsonRequest = JsonSerializer.Serialize(request, jsonOptions);
            await System.IO.File.WriteAllTextAsync(tempJsonPath, jsonRequest);

            var process = new Process
            {
                StartInfo = new ProcessStartInfo
                {
                    FileName = "python",
                    Arguments = $"script.py \"{tempJsonPath}\"",
                    WorkingDirectory = scriptDirectory,
                    RedirectStandardOutput = true,
                    RedirectStandardError = true,
                    UseShellExecute = false,
                    CreateNoWindow = true,
                }
            };

            process.Start();
            string result = await process.StandardOutput.ReadToEndAsync();
            string error = await process.StandardError.ReadToEndAsync();
            process.WaitForExit();

            // Удаляем временный файл
            if (System.IO.File.Exists(tempJsonPath))
            {
                System.IO.File.Delete(tempJsonPath);
            }

            if (process.ExitCode != 0)
            {
                return BadRequest(new { Status = "error", Error = error });
            }

            var summary = JsonSerializer.Deserialize<SummaryDataResult>(result, jsonOptions);
            var summaryData = new SummaryData
            {
                VideoName = summary.VideoName,
                RoadName = request.RoadName,
                SectionOfRoad = request.SectionOfRoad,
                RoadClass = request.RoadClass,
                RoadCategory = request.RoadCategory,
                Contractor = request.Contractor,
                CreatedAt = DateTime.UtcNow,
                ProcessedAt = null,
                IsProcessed = false
            };
            _context.SummaryData.Add(summaryData);
            await _context.SaveChangesAsync();

            return Content(result, "application/json");
        }

        public class PythonScriptRequest
        {
            public string RoadName { get; set; }
            public string SectionOfRoad { get; set; }
            public string RoadClass { get; set; }
            public string RoadCategory { get; set; }
            public string Contractor { get; set; }
            public string VideoFilePath { get; set; }
            public string TextFilePath { get; set; }
            public string CriticalLevels { get; set; }
        }

        public class SummaryDataResult
        {
            public string VideoName { get; set; }
            public string RoadName { get; set; }
            public string SectionOfRoad { get; set; }
            public Dictionary<string, int> ClassCounts { get; set; }
            public int TotalObjects { get; set; }
            public double TotalDistance { get; set; }
            public string ProcessingTime { get; set; }
            public string Status { get; set; }
            public string Error { get; set; }
        }
    }
}