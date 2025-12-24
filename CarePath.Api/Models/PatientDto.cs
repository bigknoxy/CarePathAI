using System;
using System.ComponentModel.DataAnnotations;

namespace CarePath.Api.Models
{
    /// <summary>
    /// Data Transfer Object for patient information used in API requests and responses.
    /// </summary>
    public class PatientDto
    {
        /// <summary>
        /// Gets or sets the unique identifier for the patient.
        /// </summary>
        public int Id { get; set; }

        /// <summary>
        /// Gets or sets the patient's first name.
        /// </summary>
        [Required(ErrorMessage = "First name is required")]
        public string FirstName { get; set; } = string.Empty;

        /// <summary>
        /// Gets or sets the patient's last name.
        /// </summary>
        [Required(ErrorMessage = "Last name is required")]
        public string LastName { get; set; } = string.Empty;

        /// <summary>
        /// Gets or sets the patient's date of birth.
        /// </summary>
        public DateTime? DateOfBirth { get; set; }

        /// <summary>
        /// Gets or sets the patient's medical record number.
        /// </summary>
        public string MedicalRecordNumber { get; set; } = string.Empty;
    }
}