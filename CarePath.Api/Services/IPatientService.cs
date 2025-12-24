using System.Collections.Generic;
using System.Threading.Tasks;
using CarePath.Domain.Models;
using CarePath.Api.Models;

namespace CarePath.Api.Services
{
    /// <summary>
    /// Service interface for managing patient data operations.
    /// </summary>
    public interface IPatientService
    {
        /// <summary>
        /// Gets all patients from the data store.
        /// </summary>
        /// <returns>A collection of all patients.</returns>
        Task<IEnumerable<Patient>> GetAllAsync();

        /// <summary>
        /// Gets a patient by their unique identifier.
        /// </summary>
        /// <param name="id">The patient identifier.</param>
        /// <returns>The patient if found; otherwise, null.</returns>
        Task<Patient?> GetByIdAsync(int id);

        /// <summary>
        /// Creates a new patient in the data store.
        /// </summary>
        /// <param name="dto">The patient data transfer object containing patient information.</param>
        /// <returns>The created patient with assigned identifier.</returns>
        Task<Patient> CreateAsync(PatientDto dto);
    }
}