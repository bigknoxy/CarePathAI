using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;
using CarePath.Domain.Models;
using CarePath.Api.Models;

namespace CarePath.Api.Services
{
    /// <summary>
    /// Service implementation for managing patient data operations.
    /// </summary>
    public class PatientService : IPatientService
    {
        private readonly ConcurrentDictionary<int, Patient> _patients;
        private readonly ILogger<PatientService> _logger;
        private readonly JsonSerializerOptions _jsonOptions;

        /// <summary>
        /// Initializes a new instance of the PatientService class.
        /// </summary>
        /// <param name="configuration">The application configuration.</param>
        /// <param name="logger">The logger instance.</param>
        public PatientService(IConfiguration configuration, ILogger<PatientService> logger)
        {
            _logger = logger;
            _patients = new ConcurrentDictionary<int, Patient>();
            
            _jsonOptions = new JsonSerializerOptions
            {
                PropertyNameCaseInsensitive = true,
                PropertyNamingPolicy = JsonNamingPolicy.CamelCase
            };

            LoadPatientsFromDataDirectory(configuration);
        }

        /// <summary>
        /// Gets all patients from the data store.
        /// </summary>
        /// <returns>A collection of all patients.</returns>
        public Task<IEnumerable<Patient>> GetAllAsync()
        {
            return Task.FromResult(_patients.Values.AsEnumerable());
        }

        /// <summary>
        /// Gets a patient by their unique identifier.
        /// </summary>
        /// <param name="id">The patient identifier.</param>
        /// <returns>The patient if found; otherwise, null.</returns>
        public Task<Patient?> GetByIdAsync(int id)
        {
            _patients.TryGetValue(id, out var patient);
            return Task.FromResult(patient);
        }

        /// <summary>
        /// Creates a new patient in the data store.
        /// </summary>
        /// <param name="dto">The patient data transfer object containing patient information.</param>
        /// <returns>The created patient with assigned identifier.</returns>
        public Task<Patient> CreateAsync(PatientDto dto)
        {
            var newId = _patients.Count > 0 ? _patients.Keys.Max() + 1 : 1;
            
            var patient = new Patient
            {
                Id = newId,
                FirstName = dto.FirstName,
                LastName = dto.LastName,
                DateOfBirth = dto.DateOfBirth,
                MedicalRecordNumber = dto.MedicalRecordNumber ?? $"MRN{newId:D3}",
                Conditions = new List<string>(),
                Notes = string.Empty
            };

            _patients.TryAdd(newId, patient);
            _logger.LogInformation("Created new patient with ID: {Id}", newId);

            return Task.FromResult(patient);
        }

        private void LoadPatientsFromDataDirectory(IConfiguration configuration)
        {
            try
            {
                var dataDir = configuration["CAREPATH_DATA_DIR"] ?? 
                             Path.Combine("..", "carepath_ml", "data", "synthetic");

                if (!Directory.Exists(dataDir))
                {
                    _logger.LogWarning("Data directory not found: {DataDir}", dataDir);
                    return;
                }

                var jsonFiles = Directory.GetFiles(dataDir, "*.json");
                
                foreach (var file in jsonFiles)
                {
                    try
                    {
                        var jsonContent = File.ReadAllText(file);
                        var patient = JsonSerializer.Deserialize<Patient>(jsonContent, _jsonOptions);
                        
                        if (patient != null)
                        {
                            _patients.TryAdd(patient.Id, patient);
                            _logger.LogInformation("Loaded patient {Id} from {File}", patient.Id, Path.GetFileName(file));
                        }
                    }
                    catch (JsonException ex)
                    {
                        _logger.LogError(ex, "Failed to parse JSON file: {File}", Path.GetFileName(file));
                    }
                    catch (Exception ex)
                    {
                        _logger.LogError(ex, "Error processing file: {File}", Path.GetFileName(file));
                    }
                }

                _logger.LogInformation("Loaded {Count} patients from data directory", _patients.Count);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error loading patients from data directory");
            }
        }
    }
}