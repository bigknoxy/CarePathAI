using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.Logging;
using CarePath.Api.Models;
using CarePath.Api.Services;

namespace CarePath.Api.Controllers
{
    /// <summary>
    /// Controller for managing patient-related API endpoints.
    /// </summary>
    [ApiController]
    [Route("api/[controller]")]
    public class PatientsController : ControllerBase
    {
        private readonly IPatientService _patientService;
        private readonly ILogger<PatientsController> _logger;

        /// <summary>
        /// Initializes a new instance of the PatientsController class.
        /// </summary>
        /// <param name="patientService">The patient service instance.</param>
        /// <param name="logger">The logger instance.</param>
        public PatientsController(IPatientService patientService, ILogger<PatientsController> logger)
        {
            _patientService = patientService;
            _logger = logger;
        }

        /// <summary>
        /// Gets all patients.
        /// </summary>
        /// <returns>A collection of patient DTOs.</returns>
        [HttpGet]
        public async Task<ActionResult<IEnumerable<PatientDto>>> GetAll()
        {
            try
            {
                var patients = await _patientService.GetAllAsync();
                var patientDtos = patients.Select(MapToDto);
                return Ok(patientDtos);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error retrieving all patients");
                return StatusCode(500, "Internal server error");
            }
        }

        /// <summary>
        /// Gets a patient by their unique identifier.
        /// </summary>
        /// <param name="id">The patient identifier.</param>
        /// <returns>The patient DTO if found; otherwise, NotFound.</returns>
        [HttpGet("{id}")]
        public async Task<ActionResult<PatientDto>> GetById(int id)
        {
            try
            {
                var patient = await _patientService.GetByIdAsync(id);
                if (patient == null)
                {
                    return NotFound($"Patient with ID {id} not found");
                }

                var patientDto = MapToDto(patient);
                return Ok(patientDto);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error retrieving patient with ID: {Id}", id);
                return StatusCode(500, "Internal server error");
            }
        }

        /// <summary>
        /// Creates a new patient.
        /// </summary>
        /// <param name="patientDto">The patient DTO containing patient information.</param>
        /// <returns>The created patient DTO with assigned identifier.</returns>
        [HttpPost]
        public async Task<ActionResult<PatientDto>> Create([FromBody] PatientDto patientDto)
        {
            try
            {
                if (!ModelState.IsValid)
                {
                    return BadRequest(ModelState);
                }

                var createdPatient = await _patientService.CreateAsync(patientDto);
                var createdDto = MapToDto(createdPatient);

                return CreatedAtAction(
                    nameof(GetById), 
                    new { id = createdDto.Id }, 
                    createdDto);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error creating new patient");
                return StatusCode(500, "Internal server error");
            }
        }

        private static PatientDto MapToDto(CarePath.Domain.Models.Patient patient)
        {
            return new PatientDto
            {
                Id = patient.Id,
                FirstName = patient.FirstName,
                LastName = patient.LastName,
                DateOfBirth = patient.DateOfBirth,
                MedicalRecordNumber = patient.MedicalRecordNumber
            };
        }
    }
}