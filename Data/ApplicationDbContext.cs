using Microsoft.EntityFrameworkCore;
using System.ComponentModel.DataAnnotations;

namespace AnalysisNeuralNetwork.Data
{
    public class ApplicationDbContext : DbContext
    {
        public ApplicationDbContext(DbContextOptions<ApplicationDbContext> options)
            : base(options)
        {
        }

        public DbSet<DetectedObject> DetectedObjects { get; set; }
        public DbSet<SummaryData> SummaryData { get; set; }
    }

    public class DetectedObject
    {
        [Key]
        public int ObjectId { get; set; }
        public string? Title { get; set; }
        public string? SectionOfRoad { get; set; }
        public string? ImageName { get; set; }
        public string? VideoName { get; set; }
        public string? ClassName { get; set; }
        public double Latitude { get; set; }
        public double Longitude { get; set; }
        public string? Status { get; set; }
        public int CriticalLevel { get; set; }
        public string? RoadClass { get; set; }
        public string? RoadCategory { get; set; }
        public string? Contractor { get; set; }
        public DateTime DateTimeDetection { get; set; }
    }

    public class SummaryData
    {
        [Key]
        public int Id { get; set; }
        public string? VideoName { get; set; }
        public string? RoadName { get; set; }
        public string? SectionOfRoad { get; set; }
        public string? RoadClass { get; set; }
        public string? RoadCategory { get; set; }
        public string? Contractor { get; set; }
        public DateTime CreatedAt { get; set; }
        public DateTime? ProcessedAt { get; set; }
        public bool IsProcessed { get; set; }
    }
}