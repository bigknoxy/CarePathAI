using System;
using System.Collections.Generic;

namespace CarePath.Domain.Models
{
    /// <summary>
    /// Represents a patient in the healthcare system.
    /// </summary>
    public class Patient
    {
        /// <summary>
        /// Gets or sets the unique identifier for the patient.
        /// </summary>
        public int Id { get; set; }

        /// <summary>
        /// Gets or sets the patient's first name.
        /// </summary>
        public string FirstName { get; set; } = string.Empty;

        /// <summary>
        /// Gets or sets the patient's last name.
        /// </summary>
        public string LastName { get; set; } = string.Empty;

        /// <summary>
        /// Gets or sets the patient's date of birth.
        /// </summary>
        public DateTime? DateOfBirth { get; set; }

        /// <summary>
        /// Gets or sets the patient's medical record number.
        /// </summary>
        public string MedicalRecordNumber { get; set; } = string.Empty;

        /// <summary>
        /// Gets or sets the list of patient's medical conditions.
        /// </summary>
        public List<string> Conditions { get; set; } = new List<string>();

        /// <summary>
        /// Gets or sets the patient's clinical notes.
        /// </summary>
        public string Notes { get; set; } = string.Empty;
    }
}