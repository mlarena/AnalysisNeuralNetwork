using System;
using Microsoft.EntityFrameworkCore.Migrations;
using Npgsql.EntityFrameworkCore.PostgreSQL.Metadata;

#nullable disable

namespace AnalysisNeuralNetwork.Migrations
{
    /// <inheritdoc />
    public partial class AddRoadFields : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.CreateTable(
                name: "DetectedObjects",
                columns: table => new
                {
                    ObjectId = table.Column<int>(type: "integer", nullable: false)
                        .Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                    Title = table.Column<string>(type: "text", nullable: true),
                    SectionOfRoad = table.Column<string>(type: "text", nullable: true),
                    ImageName = table.Column<string>(type: "text", nullable: true),
                    VideoName = table.Column<string>(type: "text", nullable: true),
                    ClassName = table.Column<string>(type: "text", nullable: true),
                    Latitude = table.Column<double>(type: "double precision", nullable: false),
                    Longitude = table.Column<double>(type: "double precision", nullable: false),
                    Status = table.Column<string>(type: "text", nullable: true),
                    CriticalLevel = table.Column<int>(type: "integer", nullable: false),
                    RoadClass = table.Column<string>(type: "text", nullable: true),
                    RoadCategory = table.Column<string>(type: "text", nullable: true),
                    Contractor = table.Column<string>(type: "text", nullable: true),
                    DateTimeDetection = table.Column<DateTime>(type: "timestamp with time zone", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_DetectedObjects", x => x.ObjectId);
                });

            migrationBuilder.CreateTable(
                name: "SummaryData",
                columns: table => new
                {
                    Id = table.Column<int>(type: "integer", nullable: false)
                        .Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                    VideoName = table.Column<string>(type: "text", nullable: true),
                    RoadName = table.Column<string>(type: "text", nullable: true),
                    SectionOfRoad = table.Column<string>(type: "text", nullable: true),
                    RoadClass = table.Column<string>(type: "text", nullable: true),
                    RoadCategory = table.Column<string>(type: "text", nullable: true),
                    Contractor = table.Column<string>(type: "text", nullable: true),
                    CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    ProcessedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    IsProcessed = table.Column<bool>(type: "boolean", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_SummaryData", x => x.Id);
                });
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropTable(
                name: "DetectedObjects");

            migrationBuilder.DropTable(
                name: "SummaryData");
        }
    }
}
